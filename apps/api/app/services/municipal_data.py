"""Pure deterministic geographic operations; distances are candidate screens only."""
import hashlib
import json

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform
from shapely.strtree import STRtree


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def geometry(value, crs='EPSG:4326'):
    g = shape(value)
    if g.is_empty or not g.is_valid:
        raise ValueError('Invalid source geometry')
    if crs != 'EPSG:4326':
        g = transform(Transformer.from_crs(crs, 'EPSG:4326', always_xy=True).transform, g)
    return json.loads(json.dumps(mapping(g)))


def candidate_matches(records, decisions):
    """5m minimum separation in UTM18N + exact first OFT street-code candidates.

    A shared street code identifies a street, not a segment. Never auto-accept
    candidates, even a unique nearest one. Decisions bind full record content.
    """
    project = Transformer.from_crs(4326, 32618, always_xy=True).transform
    roads = [r for r in records if r['kind'] == 'road']
    projected = {r['id']: transform(project, shape(r['geometry'])) for r in roads}
    tree=STRtree(list(projected.values()))
    by_code={}
    for i,road in enumerate(roads):
        by_code.setdefault(road['raw_identifiers'].get('street_code'),[]).append(i)
    matches = []
    used = set()
    for record in records:
        if record['kind'] not in {'permit', 'condition'}:
            continue
        g = transform(project, shape(record['geometry'])) if record['geometry'] else None
        oft = record['raw_identifiers'].get('oftcode')
        candidates = []
        eligible=tree.query(g.buffer(5)) if g is not None else by_code.get(oft[:6],[]) if oft else []
        for i in eligible:
            road=roads[int(i)]
            distance = g.distance(projected[road['id']]) if g is not None else None
            street_code = road['raw_identifiers'].get('street_code')
            code_agrees = bool(oft and street_code and oft[:6] == street_code)
            if (distance is not None and distance <= 5) or (g is None and code_agrees):
                candidates.append({'road_id': road['id'], 'distance_m': round(distance, 3) if distance is not None else None,
                    'street_code_agrees': code_agrees})
        candidates.sort(key=lambda c: c['road_id'])
        decision = decisions.get(record['id'])
        target = None
        if decision:
            used.add(record['id'])
            if decision['record_hash'] != digest(record) or not decision.get('reviewer') or not decision.get('reason'):
                raise ValueError('Stale or incomplete match review')
            target = decision['road_id']
            if target not in {c['road_id'] for c in candidates}:
                raise ValueError('Review target is not an eligible candidate')
        matches.append({'id': 'match-'+digest([record['kind'], record['id']])[:24],
            'source_kind': record['kind'], 'source_record_id': record['id'], 'target_kind': 'road',
            'target_road_id': target, 'status': 'matched' if target else 'ambiguous' if candidates else 'unmatched',
            'method': 'reviewed-candidates-v1', 'tolerance_m': 5, 'metric_crs': 'EPSG:32618',
            'candidates': candidates, 'decision': decision,
            'reason': 'Human-reviewed link' if target else 'Unreviewed candidates are not confirmed links' if candidates else 'No eligible candidate',
            'confidence': 'human_reviewed' if target else 'unconfirmed'})
    if set(decisions) != used:
        raise ValueError('Unknown match-review record')
    return matches

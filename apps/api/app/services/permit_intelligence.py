"""Permit road references and coordination screening; never work footprints or schedules."""
from collections import defaultdict
from datetime import datetime
import re

from pyproj import Transformer
from shapely.geometry import shape, box
from shapely.ops import transform
from shapely.strtree import STRtree

from app.schemas.municipal import MunicipalRecord
from app.services.municipal_data import digest
from app.services.road_intelligence import build_overlay as build_review_overlay

PARAMETERS = {'version':'permit-road-reference-v1', 'metric_crs':'EPSG:32618', 'tolerance_m':5,
    'normalization':'uppercase, punctuation to spaces, collapse whitespace; no inferred aliases',
    'candidate_rule':'union of exact normalized on-name, OFT on-code, verified geometry within 5m',
    'endpoint_rule':'from/to name or OFT code at shared LION NodeID; evidence only',
    'automatic_acceptance':False,'geometry_rule':'never infer WKT CRS; only declared EPSG:4326 source geometry',
    'scope':'partial road reference only; not a footprint', 'coordination_version':'permit-coordination-v1',
    'temporal_rule':'inclusive possible administrative-window overlap; endpoint convention unverified'}
STATUSES = ('located','candidate','unlocated','outside_coverage','invalid_evidence')

def name(value):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', value.upper())).strip() if isinstance(value,str) else ''


def candidates(roads, permits, sources, bounds):
    """Indexes retain every street-name/code competitor, including duplicate SegmentIDs."""
    if len({r['id'] for r in roads+permits}) != len(roads)+len(permits):
        raise ValueError('Duplicate input record identifier')
    by_name, by_code, nodes = defaultdict(set), defaultdict(set), defaultdict(list)
    project=Transformer.from_crs(4326,32618,always_xy=True).transform
    projected={}; by_id={r['id']:r for r in roads}
    for r in roads+permits: MunicipalRecord.model_validate(r)
    for r in sorted(roads,key=lambda r:r['id']):
        if not r['geometry']:raise ValueError('Road geometry required')
        projected[r['id']]=transform(project,shape(r['geometry']))
        by_name[name(r['values'].get('name'))].add(r['id'])
        code=r['raw_identifiers'].get('street_code')
        if code:by_code[code].add(r['id'])
        a=r['lineage'].get('raw_attributes',{})
        for node in {a.get('NodeIDFrom'),a.get('NodeIDTo')}-{None,''}:nodes[str(node)].append(r)
    road_hashes={r['id']:digest(r) for r in roads}
    ids=sorted(projected); tree=STRtree([projected[key] for key in ids]); result=[]
    for p in sorted(permits,key=lambda r:r['id']):
        v=p['values']; oft=p['raw_identifiers'].get('oftcode'); reasons=[]
        valid_oft=bool(oft and re.fullmatch(r'[0-9]{18}',oft))
        if oft and not valid_oft:reasons.append('INVALID_OFT')
        source=sources.get(p['source_revision_id'],{})
        g=None
        if p['geometry'] is not None:
            if source.get('source_crs')=='EPSG:4326':g=transform(project,shape(p['geometry']))
            else:reasons.append('GEOMETRY_CRS_UNVERIFIED')
        elif p['lineage'].get('raw_wkt'):reasons.append('WKT_CRS_UNVERIFIED')
        if g is not None and not shape(p['geometry']).intersects(box(*bounds)):
            result.append({'source_record_id':p['id'],'candidates':[],'evidence_status':'outside_coverage','reasons':['VERIFIED_GEOMETRY_OUTSIDE_COVERAGE']});continue
        source_hash=digest(p)
        on=name(v.get('on_street')); eligible=set(by_name.get(on,())) if on else set()
        if valid_oft:eligible.update(by_code.get(oft[:6],()))
        if g is not None:eligible.update(ids[int(i)] for i in tree.query(g.buffer(5)) if g.distance(projected[ids[int(i)]])<=5)
        rows=[]
        for rid in sorted(eligible):
            r=by_id[rid]; attrs=r['lineage'].get('raw_attributes',{})
            neighbors={x['id']:x for node in {attrs.get('NodeIDFrom'),attrs.get('NodeIDTo')}-{None,''} for x in nodes[str(node)] if x['id']!=rid}
            def endpoint(field,code):
                target=name(v.get(field)); values=[]
                for n in neighbors.values():
                    if target and target==name(n['values'].get('name')) or code and code==n['raw_identifiers'].get('street_code'):values.append(n['id'])
                return sorted(values)
            from_rows=endpoint('from_street',oft[6:12] if valid_oft else None)
            to_rows=endpoint('to_street',oft[12:18] if valid_oft else None)
            rows.append({'road_id':rid,'source_record_hash':source_hash,'target_record_hash':road_hashes[rid],
                'on_street_name_agrees':bool(on and on==name(r['values'].get('name'))),
                'street_code_agrees':bool(valid_oft and oft[:6]==r['raw_identifiers'].get('street_code')),
                'from_endpoint_road_ids':from_rows,'to_endpoint_road_ids':to_rows,
                'distance_m':round(g.distance(projected[rid]),3) if g is not None else None,
                'grade_agreement':'unknown','roadbed_agreement':'unknown','work_footprint':'unknown'})
        state='candidate' if rows else 'invalid_evidence' if reasons or oft and not valid_oft else 'unlocated'
        if not rows:reasons.append('NO_SUPPORTED_ROAD_CANDIDATE')
        result.append({'source_record_id':p['id'],'candidates':rows,'evidence_status':state,'reasons':reasons})
    return result


def build_overlay(snapshot_id,base,roads,permits,decisions,sources):
    matches=candidates(roads,permits,sources,base['coverage']['bbox'])
    eligible={m['source_record_id'] for m in matches if m['candidates']}
    for d in decisions:
        if not d.get('candidate_set_hash') or d.get('scope')!='partial' or d.get('source_record_id') not in eligible:
            raise ValueError('Permit review requires full candidate-set hash and justified partial road-reference scope')
    bundle=build_review_overlay(snapshot_id,base,roads,permits,decisions,source_kind='permit',
        parameters=PARAMETERS,matches=matches,contract='permit-intelligence-v1',warnings=[
            'Permit associations are partial road references; work footprints and actual schedules remain unknown.',
            'Street names, OFT and proximity never authorize automatic acceptance or excavation clearance.',
            'Local reviewer labels are not verified municipal endorsement.'])
    return bundle


def stage_overlay(repository,snapshot_id,decisions):
    base=repository.snapshot(snapshot_id); roads=repository.records(snapshot_id,'road'); permits=repository.records(snapshot_id,'permit')
    sources={sid:repository.source(snapshot_id,sid) for sid in base['source_revision_ids']}
    if any(r['contains_synthetic'] or r['classification']=='synthetic_fixture' or 'synthetic_fixture' in r['field_classifications'].values() for r in roads+permits) or any(s['query'].get('synthetic_fixture') for s in sources.values()):
        raise ValueError('Synthetic harness cannot be published as official permit intelligence')
    return build_overlay(snapshot_id,base,roads,permits,decisions,sources)


def locations(snapshot_id,base,roads,permits,sources,associations=None,release_id=None):
    matches=candidates(roads,permits,sources,base['coverage']['bbox'])
    accepted=defaultdict(list);rejected=defaultdict(list)
    for a in associations or []:
        if a['status']=='accepted':accepted[a['source_record_id']].append(a)
        if a['status']=='rejected':rejected[a['source_record_id']].append(a)
    values={}
    for m in matches:
        links=accepted[m['source_record_id']]; rejected_rows=rejected[m['source_record_id']]
        rejected_ids={a['target_road_id'] for a in rejected_rows}
        active=[c for c in m['candidates'] if c['road_id'] not in rejected_ids]
        values[m['source_record_id']]={'method_version':PARAMETERS['version'],'snapshot_id':snapshot_id,
            'permit_release_id':release_id,'status':'located' if links else 'unlocated' if m['candidates'] and not active else m['evidence_status'],
            'accepted_road_ids':sorted({a['target_road_id'] for a in links}),
            'accepted_associations':sorted(links,key=lambda a:a['id']), 'candidates':active,
            'rejected_associations':sorted(rejected_rows,key=lambda a:a['id']),
            'candidate_set_hash':digest(m['candidates']),'reasons':m['reasons']+(['ALL_CANDIDATES_REJECTED'] if m['candidates'] and not active else []),
            'location_meaning':'road reference only; work footprint unknown', 'actual_schedule':'unknown',
            'parameter_hash':digest(PARAMETERS),'classification':'derived_calculation'}
        values[m['source_record_id']]['result_hash']=digest(values[m['source_record_id']])
    return values


def administrative_window(record):
    try:
        values=[datetime.fromisoformat(record['values'][key]) for key in ['valid_from','valid_to']]
        if any(v.tzinfo is not None for v in values) or values[0]>values[1]:return None
        return values
    except (ValueError,TypeError,KeyError):return None


def coordination(selected,permits,projections,snapshot_id,release_id=None):
    """One-record bounded screen, never all-pairs, no write and no actual-work claim."""
    evidence=projections[selected['id']]; target={c['road_id'] for c in evidence['candidates']}
    window=administrative_window(selected); findings=[]
    for p in sorted(permits,key=lambda r:r['id']):
        if p['id']==selected['id']:continue
        other=projections[p['id']];shared=sorted(target & {c['road_id'] for c in other['candidates']})
        if not shared:continue
        other_window=administrative_window(p)
        relation='unknown' if window is None or other_window is None else 'possible_overlap' if max(window[0],other_window[0])<=min(window[1],other_window[1]) else 'disjoint'
        if relation=='disjoint':continue
        row={'method_version':'permit-coordination-v1','snapshot_id':snapshot_id,'permit_release_id':release_id,
            'permit_ids':sorted([selected['id'],p['id']]),'related_permit_id':p['id'],
            'shared_road_ids':shared,'spatial_basis':'shared_accepted_road_reference' if set(shared)&set(evidence['accepted_road_ids'])&set(other['accepted_road_ids']) else 'shared_candidate_road_reference',
            'administrative_window_relation':relation,'actual_work_overlap':'unknown','confirmed_conflict':False,
            'same_application':bool(selected['raw_identifiers'].get('application_tracking_id') and selected['raw_identifiers'].get('application_tracking_id')==p['raw_identifiers'].get('application_tracking_id')),
            'label':'Potential coordination screening candidate; location/schedule review required',
            'record_hashes':sorted([digest(selected),digest(p)]),'location_hashes':sorted([evidence['result_hash'],other['result_hash']]),
            'parameter_hash':digest(PARAMETERS),'utility_coverage':'unknown','classification':'derived_calculation'}
        row['id']='coord-'+digest(row)[:32];findings.append(row)
    return sorted(findings,key=lambda r:r['id'])

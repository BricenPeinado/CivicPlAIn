"""Pure M3 screening: projected geometry, deterministic rules, no HTTP/DB/LLM."""
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations

import pyproj
import shapely
from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import shape

from app.schemas.conflicts import (WorkProject, AnalysisParameters, ConflictAnalysis,
    ConflictFinding, SpatialEvidence, TemporalEvidence, IndeterminateCheck)
from app.schemas.roads import Road, Evidence
from app.services.estimates import canonical_hash

METHOD = 'conflict-screen-v1'
NUMERICAL_EPSILON_M = 1e-7  # Projection roundoff only; not source positional accuracy.
PROJECT = Transformer.from_crs('EPSG:4326', 'EPSG:32618', always_xy=True)
COVERAGE = 'Utility coverage is unknown. No conflicts detected in checked records never establishes excavation safety.'


def projected(geometry):
    return shapely.transform(shape(geometry.model_dump()), PROJECT.transform, interleaved=False)


def interval(project):
    if project.schedule_status == 'completed':
        return [project.actual_start_date, project.actual_end_date], 'actual'
    return [project.start_date, project.end_date], 'planned'


def analyze(projects: list[WorkProject], roads: list[Road], parameters: AnalysisParameters | None = None,
            sources: list[Evidence] | None = None, detected_at: datetime | None = None) -> ConflictAnalysis:
    parameters = AnalysisParameters.model_validate((parameters or AnalysisParameters()).model_dump())
    # Revalidate at the domain boundary (including models constructed via model_copy).
    projects = sorted([WorkProject.model_validate(p.model_dump()) for p in projects], key=lambda p: p.id)
    roads = sorted([Road.model_validate(r.model_dump()) for r in roads], key=lambda r: r.id)
    if not projects or len(projects) > 50 or len({p.id for p in projects}) != len(projects):
        raise ValueError('analysis requires 1–50 distinct projects')
    if len({r.id for r in roads}) != len(roads):
        raise ValueError('duplicate road IDs')
    snapshots = {p.dataset_snapshot_id for p in projects} | {r.dataset_snapshot_id for r in roads}
    if len(snapshots) != 1:
        raise ValueError('analysis inputs must share one dataset snapshot')
    by_road = {r.id: r for r in roads}
    if any(not set(p.road_segment_ids) <= by_road.keys() for p in projects):
        raise ValueError('unknown affected road reference')
    sources = sorted([Evidence.model_validate(s.model_dump()) for s in sources or []], key=lambda s: s.id)
    if len({s.id for s in sources}) != len(sources):
        raise ValueError('duplicate evidence source IDs')
    refs = {ref for p in projects for ref in p.evidence_ids} | {ref for r in roads for ref in r.evidence_ids}
    if refs != {s.id for s in sources}:
        raise ValueError('analysis requires exact source contents for all input evidence')
    detected_at = detected_at or datetime.now(timezone.utc)
    if detected_at.utcoffset() is None:
        raise ValueError('analysis timestamp must be offset-aware')
    snapshot = dict(projects=[p.model_dump(mode='json') for p in projects], roads=[r.model_dump(mode='json') for r in roads],
        sources=[s.model_dump(mode='json') for s in sources], parameters=parameters.model_dump(mode='json'),
        method_version=METHOD, exchange_crs='EPSG:4326', calculation_crs='EPSG:32618',
        libraries=dict(shapely=shapely.__version__, geos=shapely.geos_version_string, pyproj=pyproj.__version__, proj=pyproj.proj_version_str))
    input_hash = canonical_hash(snapshot)
    analysis_id = 'analysis-' + input_hash
    active = [p for p in projects if p.schedule_status != 'cancelled']
    excluded = [p.id for p in projects if p.schedule_status == 'cancelled']
    geoms = {i: projected(p.geometry) for i, p in enumerate(active) if p.geometry is not None}
    geom_ids = list(geoms)
    tree = STRtree([geoms[i] for i in geom_ids])
    candidates = set()
    # Query once per footprint; no all-pairs geometric distance scan.
    for i, geom in geoms.items():
        for idx in tree.query(geom, predicate='dwithin', distance=parameters.proximity_m + NUMERICAL_EPSILON_M):
            j = geom_ids[int(idx)]
            if i != j:
                candidates.add(tuple(sorted((i, j))))
    road_geoms = [projected(r.geometry) for r in roads]
    road_tree = STRtree(road_geoms)
    corridors = {}
    declared = defaultdict(list)
    corridor_members = defaultdict(list)
    for i, p in enumerate(active):
        for rid in p.road_segment_ids:
            declared[rid].append(i)
        corridors[i] = set()
        if i in geoms:
            corridors[i] = {roads[int(k)].id for k in road_tree.query(geoms[i], predicate='dwithin', distance=parameters.corridor_m + NUMERICAL_EPSILON_M)}
        for rid in corridors[i]:
            corridor_members[rid].append(i)
    for index in (declared, corridor_members):
        for members in index.values():
            candidates.update(combinations(sorted(members), 2))
    # Unknown locations must be compared explicitly; indexing cannot prove separation.
    for i in range(len(active)):
        if i not in geoms:
            candidates.update(tuple(sorted((i, j))) for j in range(len(active)) if j != i)
    warnings = [COVERAGE, 'Screening priorities are coordination policy, never validated safety assessments.']
    if len(active) < 2:
        warnings.append('Fewer than two non-cancelled projects; no pair comparison is possible.')
    for p in active:
        dates, _ = interval(p)
        if not p.geometry:
            warnings.append(f'{p.id}: location unknown; shared road references do not establish a work footprint.')
        if not all(dates):
            warnings.append(f'{p.id}: schedule incomplete; sequencing cannot be fully assessed.')
        if p.location_status == 'approximate':
            warnings.append(f'{p.id}: approximate footprint; positional accuracy is unverified.')
    findings, indeterminate = [], []
    for i, j in sorted(candidates):
        a, b = active[i], active[j]
        shared = sorted(set(a.road_segment_ids) & set(b.road_segment_ids))
        corridor = sorted(corridors[i] & corridors[j])
        distance, intersects, polygon_overlap = None, False, False
        if i in geoms and j in geoms:
            distance = geoms[i].distance(geoms[j])
            intersects = geoms[i].intersects(geoms[j])
            polygon_overlap = geoms[i].geom_type == geoms[j].geom_type == 'Polygon' and geoms[i].intersection(geoms[j]).area > 0
        classifications = []
        if polygon_overlap and a.location_status != 'approximate' and b.location_status != 'approximate':
            classifications.append('confirmed_geometric_overlap')
        if shared:
            classifications.append('shared_affected_road')
        if corridor or (distance is not None and distance <= parameters.proximity_m + NUMERICAL_EPSILON_M):
            if not polygon_overlap or a.location_status == 'approximate' or b.location_status == 'approximate':
                classifications.append('proximity_based_potential_overlap')
        spatial_known = bool(classifications)
        if a.geometry is None or b.geometry is None:
            classifications.append('insufficient_spatial_information')
        spatial = SpatialEvidence(classifications=classifications, distance_m=round(distance, 6) if distance is not None else None,
            polygon_overlap=polygon_overlap, geometry_intersects=intersects, shared_road_ids=shared, shared_corridor_ids=corridor,
            basis='Projected EPSG:32618; polygon area overlap, declared roads, centerline corridor screening and direct footprint distance. Geometry overlap is not field confirmation or an excavation collision.')
        da, ba = interval(a)
        db, bb = interval(b)
        missing = [f'{p.id}.geometry' for p in (a, b) if p.geometry is None]
        missing += [f'{p.id}.{basis}_{field}' for p, dates, basis in [(a, da, ba), (b, db, bb)] for field, value in zip(('start_date', 'end_date'), dates) if value is None]
        if missing:
            indeterminate.append(IndeterminateCheck(project_ids=[a.id, b.id], missing_fields=missing,
                reason='Incomplete evidence; known shared-road findings may coexist with unknown footprint or schedule checks.', spatial_evidence=spatial))
        if not spatial_known or not all(da + db):
            continue
        temporal = TemporalEvidence(intervals={a.id: da, b.id: db}, interval_basis={a.id: ba, b.id: bb})
        overlap_start, overlap_end = max(da[0], db[0]), min(da[1], db[1])
        kinds = []
        if overlap_start < overlap_end and a.schedule_status != 'completed' and b.schedule_status != 'completed':
            temporal.overlap_start, temporal.overlap_end = overlap_start, overlap_end
            kinds.append(('concurrent_work', 'Supplied work areas or roads are related and scheduled intervals overlap. Coordinate the actual scopes; physical excavation interference is unverified.'))
            if (a.lanes_closed or 0) > 0 and (b.lanes_closed or 0) > 0 and (shared or corridor):
                kinds.append(('multiple_closures', 'Both records declare lane closures on a shared road or screened corridor during overlapping dates. Review access, traffic management and grade separation.'))
        elif overlap_start >= overlap_end:
            first, second, d1, d2 = (a, b, da, db) if da[1] <= db[0] else (b, a, db, da)
            gap = (d2[0] - d1[1]).days
            if 0 <= gap <= parameters.reopening_horizon_days and second.schedule_status != 'completed':
                temporal.gap_days, temporal.preceding_project_id = gap, first.id
                if first.kind == 'road_repair' and first.work_type in ('resurfacing', 'reconstruction') and second.kind == 'utility' and (second.excavation_required is True or (second.work_type == 'excavation' and second.excavation_required is not False)):
                    kinds.append(('reopening_risk', 'Road repair precedes spatially related potential utility excavation within the review window. Potential pavement rework requires inspection of actual excavation and restoration scope; damage and financial loss are not established.'))
                else:
                    kinds.append(('sequencing_review', 'Related work is scheduled within the sequencing review window. Review scope and coordination; no pavement damage is inferred.'))
        pair_warnings = []
        for p in (a, b):
            pair_warnings.extend(f'{p.id}: {note}' for note in p.limitations)
            if p.geometry is None or p.location_status == 'approximate':
                pair_warnings.append(f'{p.id}: footprint is unknown or approximate.')
            if p.schedule_basis in ('unknown', 'permit_window', 'assumed_demo'):
                pair_warnings.append(f'{p.id}: schedule basis is {p.schedule_basis}; actual work timing requires verification.')
            if p.kind == 'utility' and p.excavation_required is None:
                pair_warnings.append(f'{p.id}: excavation requirement is unknown.')
        if not polygon_overlap:
            pair_warnings.append('Shared roads, line intersections and corridor proximity do not prove overlapping excavation; depth and grade are unknown.')
        road_ids = sorted(set(a.road_segment_ids) | set(b.road_segment_ids) | set(corridor))
        evidence_ids = sorted(set(a.evidence_ids + b.evidence_ids + [e for rid in road_ids for e in by_road[rid].evidence_ids]))
        for kind, explanation in kinds:
            findings.append(ConflictFinding(id='conflict-' + canonical_hash([input_hash, a.id, b.id, kind]), analysis_id=analysis_id,
                project_ids=[a.id, b.id], affected_road_ids=road_ids, finding_type=kind,
                spatial_evidence=spatial, temporal_evidence=temporal, explanation=explanation,
                required_review=['Verify work footprint, utility location/depth, grade separation and actual excavation scope.', 'Confirm schedules with responsible organizations and coordinate access; qualified humans decide permissible work.'],
                data_quality_warnings=sorted(set(pair_warnings)), evidence_ids=evidence_ids, method_version=METHOD,
                input_hash=input_hash, detected_at=detected_at, synthetic_input=a.synthetic_input or b.synthetic_input or any(by_road[rid].synthetic_input for rid in road_ids)
                    or any(s.verification_status == 'synthetic_demo' for s in sources if s.id in evidence_ids)))
    findings.sort(key=lambda f: f.id)
    result = dict(findings=[f.model_dump(mode='json', exclude={'detected_at'}) for f in findings],
        indeterminate_checks=[c.model_dump(mode='json') for c in indeterminate], excluded_project_ids=excluded,
        possible_pair_count=len(active) * (len(active) - 1) // 2, checked_pair_count=len(candidates), warnings=warnings)
    return ConflictAnalysis(id=analysis_id, dataset_snapshot_id=projects[0].dataset_snapshot_id, findings=findings,
        indeterminate_checks=indeterminate, excluded_project_ids=excluded, possible_pair_count=result['possible_pair_count'],
        checked_pair_count=len(candidates), warnings=warnings, parameters=parameters, method_version=METHOD,
        detected_at=detected_at, input_snapshot=snapshot, input_hash=input_hash, result_hash=canonical_hash(result))

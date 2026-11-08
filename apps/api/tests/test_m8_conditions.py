"""Synthetic source-shaped records only; never official coverage evidence."""
import copy
import pytest
from app.services.road_conditions import summarize
from app.services.municipal_data import candidate_matches, digest
from test_m7_ingestion import staged, fixture_bundle


def inputs():
    r={'id':'synthetic-condition','source_revision_id':'test','lineage':{'raw_fields':{'ismultipass':'0'}},'values':{'rating':'7.52','inspection_at':'2026-01-01T12:00:00','direction':'East','road_type':'Main','non_rating_reason':None}}
    m={r['id']:{'id':'test-match','status':'matched','method':'reviewed-candidates-v2','target_road_id':'road','decision':{'scope':'whole_road'}}}
    return r,m


def test_raw_decimal_recency_and_replay():
    r,m=inputs(); a=summarize([r],m,'road','snapshot','2026-01-11',10)
    assert a['rating']=='7.52' and a['category']=='unknown' and a['age_days']==10 and not a['stale']
    assert summarize([r],m,'road','snapshot','2026-01-12',10)['stale']
    assert summarize([r],m,'road','snapshot','2026-01-11',10)==a


@pytest.mark.parametrize('rating',['0','2.699','2.7','3','3.01','3.5','3.99','4','6.7','6.99','7','7.01','7.999','8','10'])
def test_no_unsupported_decimal_classification(rating):
    r,m=inputs();r['values']['rating']=rating
    result=summarize([r],m,'road','snapshot','2026-01-11')
    assert result['category']=='unknown'
    assert result['rating']==(rating if float(rating)>=1 else None)
    assert result['history'][0]['rating']==rating


@pytest.mark.parametrize('field,value,reason', [('rating',None,'UNRATED'),('inspection_at',None,'UNDATED'),('inspection_at','2027-01-01','AFTER_AS_OF_DATE'),('non_rating_reason','Weather','NON_RATING_REASON_UNRESOLVED')])
def test_ineligible(field,value,reason):
    r,m=inputs();r['values'][field]=value
    result=summarize([r],m,'road','snapshot','2026-01-11')
    assert result['rating'] is None and result['history'][0]['reason']==reason


def test_unaccepted_partial_conflicting_and_direction_streams():
    r,m=inputs();m[r['id']]['status']='ambiguous'
    assert not summarize([r],m,'road','snapshot','2026-01-11')['history']
    m[r['id']]['status']='matched';m[r['id']]['decision']['scope']='partial'
    assert summarize([r],m,'road','snapshot','2026-01-11')['rating'] is None
    m[r['id']]['decision']['scope']='whole_road'
    b=copy.deepcopy(r);b['id']='second';m[b['id']]=m[r['id']];b['values']['rating']='4'
    assert summarize([r,b],m,'road','snapshot','2026-01-11')['reason']=='CONFLICTING_LATEST_RATINGS'
    b['values']['direction']='West'
    assert summarize([r,b],m,'road','snapshot','2026-01-11')['reason']=='MULTIPLE_DIRECTION_OR_ROADBED_STREAMS'


def test_latest_and_order_independence():
    r,m=inputs();b=copy.deepcopy(r);b['id']='older';b['values']['inspection_at']='2025-01-01';b['values']['rating']='4';m[b['id']]=m[r['id']]
    a=summarize([r,b],m,'road','snapshot','2026-01-11')
    assert a['rating']=='7.52' and a==summarize([b,r],m,'road','snapshot','2026-01-11')


def test_review_v2_binds_target_and_scope(staged):
    road=next(r for r in staged['records'] if r['kind']=='road'); r=next(r for r in staged['records'] if r['kind']=='condition')
    matches=candidate_matches(staged['records'],{},'reviewed-candidates-v2')
    c=next(m for m in matches if m['source_record_id']==r['id'])['candidates'][0]
    assert c['road_coverage_fraction']>0.99 and c['grade_agreement']=='unknown'
    d={r['id']:{'road_id':road['id'],'record_hash':digest(r),'target_record_hash':digest(road),'scope':'whole_road','scope_reason':'Synthetic equal scope','reviewer':'Synthetic reviewer','reason':'Synthetic test'}}
    assert next(m for m in candidate_matches(staged['records'],d,'reviewed-candidates-v2') if m['source_record_id']==r['id'])['status']=='matched'
    d[r['id']]['target_record_hash']='stale'
    with pytest.raises(ValueError):candidate_matches(staged['records'],d,'reviewed-candidates-v2')


def test_duplicates_and_review_provenance():
    r,m=inputs()
    a=summarize([r],m,'road','snapshot','2026-01-11')
    assert summarize([r,r],m,'road','snapshot','2026-01-11')==a
    b=copy.deepcopy(r);b['values']['rating']='2'
    with pytest.raises(ValueError,match='duplicate'):
        summarize([r,b],m,'road','snapshot','2026-01-11')
    m[r['id']]['decision']['reason']='Different review evidence'
    b=summarize([r],m,'road','snapshot','2026-01-11')
    assert a['rating']==b['rating'] and a['input_hash']!=b['input_hash']


def test_missing_direction_multipass_and_legacy_review_are_not_current():
    r,m=inputs();r['values']['direction']=None
    assert summarize([r],m,'road','snapshot','2026-01-11')['history'][0]['reason']=='UNKNOWN_DIRECTION_OR_ROADBED'
    r,m=inputs();r['lineage']={'raw_fields':{'ismultipass':'1'}}
    assert summarize([r],m,'road','snapshot','2026-01-11')['history'][0]['reason']=='MULTIPASS_SELECTION_UNRESOLVED'
    r,m=inputs();m[r['id']]['method']='reviewed-candidates-v1'
    assert summarize([r],m,'road','snapshot','2026-01-11')['rating'] is None


def test_parallel_crossing_and_duplicate_identifiers_stay_candidates(staged):
    road=next(r for r in staged['records'] if r['kind']=='road')
    condition=next(r for r in staged['records'] if r['kind']=='condition')
    parallel=copy.deepcopy(road);parallel['id']='parallel-row'
    # About 2m lateral separation. Same identifier is intentionally inconclusive.
    parallel['geometry']['coordinates'][0]=[[x,y+.00002] for x,y in road['geometry']['coordinates'][0]]
    crossing=copy.deepcopy(road);crossing['id']='crossing-row'
    crossing['geometry']['coordinates']=[[[-74.0095,40.7115],[-74.0095,40.7125]]]
    distant=copy.deepcopy(road);distant['id']='distant-row'
    distant['geometry']['coordinates']=[[[-74.01,40.72],[-74.009,40.72]]]
    from shapely.geometry import shape
    for row in [parallel,crossing,distant]:row['bbox']=list(shape(row['geometry']).bounds)
    a=candidate_matches([road,parallel,crossing,distant,condition],{},'reviewed-candidates-v2')[0]
    assert a['status']=='ambiguous' and a['target_road_id'] is None
    by_id={c['road_id']:c for c in a['candidates']}
    assert set(by_id)=={road['id'],parallel['id'],crossing['id']}
    assert by_id[crossing['id']]['road_coverage_fraction']<0.2
    assert by_id[parallel['id']]['road_coverage_fraction']>0.99
    assert a==candidate_matches([distant,crossing,parallel,road,condition],{},'reviewed-candidates-v2')[0]


def test_legacy_stage_replay_is_unchanged(tmp_path):
    from app.ingestion.pipeline import stage
    path=fixture_bundle(tmp_path)
    old=stage(path)
    assert old==stage(path)
    assert old['manifest']['matching_version']=='reviewed-candidates-v1'


def test_equivalent_timestamp_formats_conflict_and_invalid_source_time():
    r,m=inputs();b=copy.deepcopy(r);b['id']='second';b['values']['inspection_at']='2026-01-01T12:00:00.000';b['values']['rating']='1';m[b['id']]=m[r['id']]
    assert summarize([r,b],m,'road','snapshot','2026-01-11')['reason']=='CONFLICTING_LATEST_RATINGS'
    r['values']['inspection_at']='2026-01-01T12:00:00Z'
    assert summarize([r],m,'road','snapshot','2026-01-11')['rating'] is None
    r['values']['inspection_at']='invalid'
    assert summarize([r],m,'road','snapshot','2026-01-11')['history'][0]['reason']=='INVALID_RATING_OR_DATE'


def test_geometry_validation_duplicate_input_ids_and_zero_rating(staged):
    r,m=inputs();r['values']['rating']='0'
    result=summarize([r],m,'road','snapshot','2026-01-11')
    assert result['rating'] is None and result['history'][0]['rating']=='0'
    assert result['history'][0]['reason']=='RATING_VALIDITY_UNRESOLVED'
    records=copy.deepcopy(staged['records'])
    road=next(r for r in records if r['kind']=='road')
    with pytest.raises(ValueError,match='Duplicate'):
        candidate_matches(records+[road],{},'reviewed-candidates-v2')
    road['geometry']={'type':'MultiLineString','coordinates':[[[-74.01,40.71],[-74.01,40.71]]]}
    with pytest.raises(ValueError):candidate_matches(records,{},'reviewed-candidates-v2')


def test_duplicate_assessment_values_use_stable_id_without_averaging():
    r,m=inputs();b=copy.deepcopy(r);b['id']='second';m[b['id']]=m[r['id']]
    a=summarize([r,b],m,'road','snapshot','2026-01-11')
    assert a['latest_usable_id']=='second' and a['rating']=='7.52' and len(a['history'])==2
    assert a==summarize([b,r],m,'road','snapshot','2026-01-11')

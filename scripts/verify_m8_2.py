"""Offline permit coverage verification; read-only database, exclusive report, no approval.

PYTHONPATH=apps/api .venv/bin/python scripts/verify_m8_2.py --help
"""
import argparse
from collections import Counter
from pathlib import Path
import json
import re
import time

from verify_m8_1 import ReadOnlyEvidence,verify_archive
from app.ingestion.pipeline import stage
from app.services.municipal_data import digest
from app.services.permit_intelligence import stage_overlay,locations,coordination,administrative_window,STATUSES,PARAMETERS


def verify(database,snapshot,acquisition_path,bundle_path):
    acquisition,checked=verify_archive(acquisition_path)
    repository=ReadOnlyEvidence(database,snapshot)
    try:
        staged=stage(acquisition_path,{})
        if staged['snapshot_id']!=snapshot or staged['manifest']!=repository.base:
            raise ValueError('Archive does not reproduce pinned snapshot')
        stored=[r for kind in ['road','permit','condition','context'] for r in repository.records(snapshot,kind)]
        if sorted(stored,key=lambda r:r['id'])!=sorted(staged['records'],key=lambda r:r['id']):
            raise ValueError('Stored import rows differ from adapter replay')
        bundle=json.loads(bundle_path.read_text())
        decisions=[r['decision'] for r in bundle['associations'] if r['decision']]
        if stage_overlay(repository,snapshot,decisions)!=bundle:
            raise ValueError('Permit release does not reproduce')
        stored_release=repository.conn.execute('SELECT manifest_json FROM intelligence_releases WHERE id=? AND base_snapshot_id=?',(bundle['report']['release_id'],snapshot)).fetchone()
        if stored_release is None or json.loads(stored_release[0])!=bundle['manifest']:
            raise ValueError('Published release differs from replay bundle')
        stored_associations=[json.loads(r[0]) for r in repository.conn.execute('SELECT payload FROM permit_associations WHERE release_id=? AND base_snapshot_id=? ORDER BY id',(bundle['report']['release_id'],snapshot))]
        if stored_associations!=bundle['associations']:raise ValueError('Stored associations differ from replay')
        roads=repository.records(snapshot,'road');permits=repository.records(snapshot,'permit')
        sources={sid:repository.source(snapshot,sid) for sid in repository.base['source_revision_ids']}
        started=time.monotonic()
        evidence=locations(snapshot,repository.base,roads,permits,sources,bundle['associations'],bundle['report']['release_id'])
        elapsed=time.monotonic()-started
        counts=Counter(e['status'] for e in evidence.values());total=len(permits)
        def metric(n):return {'count':n,'percent':round(100*n/total,4) if total else None,'denominator':total}
        oft=[p['raw_identifiers'].get('oftcode') for p in permits];valid=[v for v in oft if v and re.fullmatch(r'[0-9]{18}',v)]
        per_candidate=Counter(len(e['candidates']) for e in evidence.values())
        accepted=[a for a in bundle['associations'] if a['status']=='accepted']
        reasons=Counter(reason for e in evidence.values() for reason in e['reasons'])
        # New-window report counts older-but-administratively-overlapping records, not actual active work.
        start=acquisition.get('permit_window',{}).get('start')
        older=[p for p in permits if p['values'].get('issued_at') and p['values']['issued_at']<'2026-01-01']
        # Select the most ambiguous imported record deterministically to demonstrate bounded screening.
        selected=max(permits,key=lambda p:(len(evidence[p['id']]['candidates']),p['id'])) if permits else None
        screening=coordination(selected,permits,evidence,snapshot,bundle['report']['release_id']) if selected else []
        result={'contract_version':'permit-verification-v1','snapshot_id':snapshot,'permit_release_id':bundle['report']['release_id'],
            'parameters':PARAMETERS,'parameter_hash':digest(PARAMETERS),'source_revision_ids':repository.base['source_revision_ids'],
            'archived_file_hashes':checked,'archive_replay':'PASS','overlay_replay':'PASS','total_permits':total,
            'status_counts':{s:metric(counts[s]) for s in STATUSES},'accepted_links':len(accepted),
            'accepted_distinct_roads':len({a['target_road_id'] for a in accepted}),
            'oft_valid':metric(len(valid)),'oft_missing':metric(sum(not v for v in oft)),
            'oft_invalid':metric(sum(bool(v) and not re.fullmatch(r'[0-9]{18}',v) for v in oft)),
            'oft_duplicate_value_groups':sum(n>1 for n in Counter(valid).values()),
            'raw_wkt_present':metric(sum(bool(p['lineage'].get('raw_wkt')) for p in permits)),
            'usable_geometry':metric(sum(p['geometry'] is not None and sources[p['source_revision_id']]['source_crs']=='EPSG:4326' for p in permits)),
            'issued_before_2026_01_01':metric(len(older)),'window_start':start,
            'candidate_count_distribution':dict(sorted(per_candidate.items())),'reason_counts':dict(sorted(reasons.items())),
            'precision':{'status':'unmeasured','independent_reviewed_labels':0,'automatic_acceptance':False},
            'source_status_counts':dict(Counter(p['values'].get('permit_status') or '(missing)' for p in permits)),
            'administrative_window_unknown':metric(sum(administrative_window(p) is None for p in permits)),
            'issue_date_missing':metric(sum(not p['values'].get('issued_at') for p in permits)),
            'application_id_duplicate_groups':sum(n>1 for n in Counter(p['raw_identifiers'].get('application_tracking_id') for p in permits if p['raw_identifiers'].get('application_tracking_id')).values()),
            'actual_schedule_known':0,'sample_screen':{'selection':'maximum candidate degree, stable ID tie break',
                'permit_id':selected['id'] if selected else None,'candidate_roads':len(evidence[selected['id']]['candidates']) if selected else 0,
                'screening_candidates':len(screening),'result_hash':digest(screening),'confirmed_conflicts':0},
            'projection_hash':digest(evidence),'limitations':['Administrative window is not an active-work census; older missing validity records may be omitted.',
                'No WKT CRS verified. No absence-of-work or excavation-safety conclusion.',
                'Name/code-only candidates do not establish geographic membership, construction footprint or precision.'],
            'verification_hash':None}
        result['verification_hash']=digest({k:v for k,v in result.items() if k!='verification_hash'})
        return result,elapsed
    finally:repository.conn.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ['database','acquisition','bundle','report']:parser.add_argument('--'+arg,type=Path,required=True)
    parser.add_argument('--snapshot',required=True)
    args=parser.parse_args()
    if args.report.exists():raise ValueError('Refusing report overwrite')
    result,elapsed=verify(args.database,args.snapshot,args.acquisition,args.bundle)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'verification_hash':result['verification_hash'],'total_permits':result['total_permits'],
        'status_counts':result['status_counts'],'projection_seconds_observed':round(elapsed,3)}))

if __name__=='__main__':main()

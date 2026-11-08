"""Read-only saved official screening replay; never approves supplied evidence or work."""
import argparse,json,sqlite3
from pathlib import Path
from collections import Counter
from app.core.official_screening_repository import OfficialScreeningRepository
from app.services.municipal_data import digest


def verify(database,snapshot):
    with sqlite3.connect('file:'+str(database.resolve())+'?mode=ro',uri=True) as conn:
        conn.execute('PRAGMA query_only=ON')
        if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or conn.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Integrity failure')
        saved=conn.execute('SELECT payload FROM official_screenings WHERE snapshot_id=? ORDER BY id',(snapshot,)).fetchall()
        if not saved:raise ValueError('No saved screenings in selected snapshot')
        output=[]
        for (payload,) in saved:
            record=json.loads(payload);OfficialScreeningRepository(database).verify(record);inputs=record['input_snapshot']
            for row in [*inputs['roads'],*[p['record'] for p in inputs['permits']]]:
                raw=conn.execute('SELECT payload FROM import_records WHERE snapshot_id=? AND kind=? AND id=?',(snapshot,row['kind'],row['id'])).fetchone()
                if not raw or json.loads(raw[0])!=row:raise ValueError('Pinned import differs from frozen input')
            for key,source in inputs['sources'].items():
                raw=conn.execute('SELECT payload FROM source_revisions WHERE id=?',(key,)).fetchone()
                if not raw or json.loads(raw[0])!=source:raise ValueError('Pinned source differs')
            if inputs['estimate']:
                raw=conn.execute('SELECT payload FROM municipal_estimates WHERE snapshot_id=? AND id=?',(snapshot,inputs['estimate']['id'])).fetchone()
                if not raw or json.loads(raw[0])!=inputs['estimate']:raise ValueError('Pinned estimate differs')
            result=record['result'];base=result['base'];permits=[a for a in base['activities'] if a['origin']=='administrative_permit']
            notes=[json.loads(r[0]) for r in conn.execute('SELECT payload FROM official_screening_notes WHERE screening_id=?',(record['id'],))]
            valid_findings={f['id'] for f in base['findings']}|{f['id'] for a in result['alternatives'] for f in a['screen']['findings']}
            for note in notes:
                if note['snapshot_id']!=snapshot or note['screening_id']!=record['id'] or note['finding_id'] and note['finding_id'] not in valid_findings:raise ValueError('Review reference mismatch')
                material={k:v for k,v in note.items() if k not in ['id','created_at','meaning']}
                if note['id']!='review-'+digest(material):raise ValueError('Review hash mismatch')
            output.append({'id':record['id'],'input_hash':record['input_hash'],'result_hash':record['result_hash'],
                'work_declarations':result['coverage']['selected_work_declarations'],'selected_permits':len(permits),
                'permit_location_status_counts':dict(sorted(Counter(p['permit_location']['status'] for p in permits).items())),
                'permits_promoted_to_work_footprints_or_schedules':sum(p['location'] is not None or p['schedule'] is not None for p in permits),
                'possible_pairs':base['possible_pair_count'],'checked_pairs':base['checked_pair_count'],'indeterminate_pairs':base['indeterminate_pair_count'],
                'finding_types':dict(sorted(Counter(f['finding_type'] for f in base['findings']).items())),
                'finding_categories':dict(sorted(Counter(f['category'] for f in base['findings']).items())),
                'alternatives':[{'id':a['id'],'result_hash':a['result_hash'],'findings':len(a['screen']['findings']),'indeterminate_pairs':a['screen']['indeterminate_pair_count']} for a in result['alternatives']],
                'cost_comparison':result['cost_comparison'],'review_notes':len(notes),'replay':'PASS','pinned_evidence':'PASS',
                'other_bases_isolated':[r[0] for r in conn.execute('SELECT id FROM data_snapshots WHERE id<>? ORDER BY id',(snapshot,))]})
        report={'contract_version':'screening-verification-v1','snapshot_id':snapshot,'mode':'read_only_offline_no_approval',
            'database_integrity':'PASS','saved_runs':len(output),'runs':output,
            'interpretation':'Agent QA work/schedules/cost additions are explicit technical assumptions, not documented actual construction, approved municipal inputs or independent review. No finding is excavation clearance.'}
        return report|{'verification_hash':digest(report)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--database',type=Path,required=True);parser.add_argument('--snapshot',required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise ValueError('Refusing report overwrite')
    report=verify(args.database,args.snapshot);args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'saved_runs':report['saved_runs'],'verification_hash':report['verification_hash']}))
if __name__=='__main__':main()

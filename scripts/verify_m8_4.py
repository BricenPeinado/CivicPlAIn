"""Read-only offline ranking verification. Replays inputs, never approves policy or data."""
import argparse,json,sqlite3
from pathlib import Path
from app.core.prioritization_repository import PrioritizationRepository
from app.services.municipal_data import digest


def verify(database,snapshot):
    with sqlite3.connect('file:'+str(database.resolve())+'?mode=ro',uri=True) as conn:
        conn.execute('PRAGMA query_only=ON')
        if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or conn.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Integrity failure')
        rows=conn.execute('SELECT payload FROM prioritization_runs WHERE snapshot_id=? ORDER BY id',(snapshot,)).fetchall()
        if not rows:raise ValueError('No saved priority runs in selected snapshot')
        output=[]
        for (payload,) in rows:
            record=json.loads(payload);PrioritizationRepository(database).verify(record);inputs=record['input_snapshot']
            for item in inputs['roads']:
                road=item['road'];stored=conn.execute("SELECT payload FROM import_records WHERE snapshot_id=? AND kind='road' AND id=?",(snapshot,road['id'])).fetchone()
                if not stored or json.loads(stored[0])!=road:raise ValueError('Pinned road differs from frozen row')
                for condition in item['condition_records']:
                    stored=conn.execute("SELECT payload FROM import_records WHERE snapshot_id=? AND kind='condition' AND id=?",(snapshot,condition['id'])).fetchone()
                    if not stored or json.loads(stored[0])!=condition:raise ValueError('Pinned assessment differs from frozen evidence')
            for key,source in inputs['sources'].items():
                stored=conn.execute('SELECT payload FROM source_revisions WHERE id=?',(key,)).fetchone()
                if not stored or json.loads(stored[0])!=source:raise ValueError('Pinned source differs')
            other=[r[0] for r in conn.execute('SELECT id FROM data_snapshots WHERE id<>? ORDER BY id',(snapshot,))]
            for sid in other:
                if conn.execute('SELECT 1 FROM prioritization_runs WHERE snapshot_id=? AND id=?',(sid,record['id'])).fetchone():raise ValueError('Cross-snapshot leak')
            result=record['result'];base=result['base']
            output.append({'id':record['id'],'input_hash':record['input_hash'],'result_hash':record['result_hash'],'policy_hash':base['policy_hash'],
                'objective':base['objective'],'scoped_road_rows':len(base['rows']),'ranked':base['ranked'],'unranked':base['unranked'],
                'distinct_rank_values':sorted({r['rank'] for r in base['rows'] if r['rank'] is not None}),
                'eligible_official_condition_rows':sum(r['completeness']['eligible_official_condition'] for r in base['rows']),
                'selected_cost_rows':sum(r['implementation_cost'] is not None for r in base['rows']),
                'verified_coordination_opportunities':sum(r['coordination']['verified_opportunity'] is not None for r in base['rows']),
                'sensitivity':[{'policy_hash':s['policy_hash'],'result_hash':s['result_hash'],'ranked':s['ranked'],'unranked':s['unranked']} for s in result['sensitivity']],
                'replay':'PASS','pinned_evidence':'PASS','other_existing_snapshots_isolated':other})
        report={'contract_version':'priority-verification-v1','snapshot_id':snapshot,'mode':'read_only_offline_no_approval','database_integrity':'PASS',
            'interpretation':'Technical QA policies are not independently reviewed municipal policies. Ranking unknown evidence does not establish pavement need, risk or an optimal schedule.',
            'saved_runs':len(output),'runs':output}
        return report|{'verification_hash':digest(report)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True);parser.add_argument('--snapshot',required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise ValueError('Refusing report overwrite')
    report=verify(args.database,args.snapshot);args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps({'saved_runs':report['saved_runs'],'verification_hash':report['verification_hash']}))

if __name__=='__main__':main()

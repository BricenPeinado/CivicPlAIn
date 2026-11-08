"""Offline, read-only verification of saved M8.3 snapshots. Never approves inputs.

PYTHONPATH=apps/api .venv/bin/python scripts/verify_m8_3.py --help
"""
import argparse
import json
import sqlite3
from pathlib import Path
from app.core.municipal_planning_repository import MunicipalPlanningRepository
from app.services.municipal_data import digest


def verify(database, snapshot):
    with sqlite3.connect('file:'+str(database.resolve())+'?mode=ro',uri=True) as conn:
        conn.execute('PRAGMA query_only=ON')
        if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or conn.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Database integrity failure')
        records=[json.loads(r[0]) for r in conn.execute('SELECT payload FROM municipal_estimates WHERE snapshot_id=? ORDER BY id',(snapshot,))]
        if not records:raise ValueError('No estimates in selected snapshot')
        checks=[]
        for record in records:
            # verify() is pure replay; it does not open a repository connection.
            MunicipalPlanningRepository(database).verify(record)
            frozen=record['input_snapshot'];road=frozen['road']
            stored=conn.execute("SELECT payload FROM import_records WHERE snapshot_id=? AND kind='road' AND id=?",(snapshot,road['id'])).fetchone()
            source=conn.execute('SELECT payload FROM source_revisions WHERE id=?',(road['source_revision_id'],)).fetchone()
            if not stored or json.loads(stored[0])!=road or not source or json.loads(source[0])!=frozen['road_source']:
                raise ValueError('Frozen road/source differs from pinned imported evidence')
            foreign=[]
            for (other,) in conn.execute('SELECT id FROM data_snapshots WHERE id<>? ORDER BY id',(snapshot,)):
                if conn.execute('SELECT 1 FROM municipal_estimates WHERE snapshot_id=? AND id=?',(other,record['id'])).fetchone():
                    raise ValueError('Estimate leaked across snapshots')
                foreign.append(other)
            checks.append({'id':record['id'],'road_id':road['id'],'input_hash':record['input_hash'],'result_hash':record['result_hash'],
                'replay':'PASS','pinned_road_source':'PASS','other_existing_snapshots_isolated':foreign,
                'alternatives':[{k:a[k] for k in ['treatment','quantity_m2','status','duration']}|{'totals_usd':{k:v['total_usd'] for k,v in a['cases'].items()}} for a in record['result']['alternatives']],
                'human_review':'Not approved; inspect input evidence. Hash equality does not establish truthful measurements or prices.'})
        report={'contract_version':'municipal-estimate-verification-v1','snapshot_id':snapshot,'schema_version':10,
            'verification_mode':'read_only_offline_no_approval','database_integrity':'PASS','saved_records':len(checks),'records':checks}
        return report|{'verification_hash':digest(report)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True);parser.add_argument('--snapshot',required=True)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise ValueError('Refusing report overwrite')
    report=verify(args.database,args.snapshot)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'saved_records':report['saved_records'],'verification_hash':report['verification_hash']}))

if __name__=='__main__':main()

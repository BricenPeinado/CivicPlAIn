"""Read-only pinned integration verification; no AI audit, calculation save or migration.
Output is an aggregate technical report, never government data approval.
"""
import argparse,json,sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings
from app.core.municipal_planning_repository import MunicipalPlanningRepository
from app.core.prioritization_repository import PrioritizationRepository
from app.core.official_screening_repository import OfficialScreeningRepository
from app.services.ai.official_evidence import build
from app.services.municipal_data import digest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--database',type=Path,required=True);parser.add_argument('--snapshot',required=True);parser.add_argument('--as-of',required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if not args.database.exists() or args.report.exists():raise SystemExit('Database required; report must be a new path')
    def state():
        with sqlite3.connect('file:'+str(args.database.resolve())+'?mode=ro',uri=True) as conn:
            return {table:conn.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ['import_records','municipal_estimates','prioritization_runs','official_screenings','official_screening_notes','ai_interactions']}
    before=state();results={}
    with TestClient(create_app(Settings(database_path=args.database))) as client:
        response=client.get('/api/v2/planning/decision-support',params={'snapshot_id':args.snapshot,'as_of_date':args.as_of});response.raise_for_status();summary=response.json()['data']
        for kind,repo in {'estimate':MunicipalPlanningRepository(args.database),'priority':PrioritizationRepository(args.database),'screening':OfficialScreeningRepository(args.database)}.items():
            rows=[]
            for item in repo.summaries(args.snapshot):
                record=repo.get(args.snapshot,item['id']);package=build(kind,record)
                row={'id':record['id'],'input_hash':record['input_hash'],'result_hash':record['result_hash'],'explanation_evidence_hash':package.snapshot_hash,'projected_fact_count':len(package.facts)}
                if kind=='estimate':row['alternatives']=[{'treatment':a['treatment'],'base_usd':a['cases']['base']['total_usd'],'duration':a['duration']} for a in record['result']['alternatives']]
                elif kind=='priority':row['ranked']=record['result']['base']['ranked'];row['unranked']=record['result']['base']['unranked']
                else:row['findings']=len(record['result']['base']['findings']);row['indeterminate_pairs']=record['result']['base']['indeterminate_pair_count'];row['alternatives']=[{'id':v['id'],'findings':len(v['screen']['findings']),'indeterminate_pairs':v['screen']['indeterminate_pair_count']} for v in record['result']['alternatives']]
                rows.append(row)
            results[kind]=rows
    assert before==state(),'Read-only verification changed record counts'
    report={'version':'m86-integration-qa-v1','technical_qa_only':True,'independent_municipal_review':False,'snapshot':args.snapshot,'as_of':args.as_of,'summary':summary,'replayed':results,'storage_counts_unchanged':True,'counts':before,'utility_coverage':'unknown','actual_work_conflict_coverage':'unavailable'}
    report['report_hash']=digest(report);args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(args.report),'hash':report['report_hash'],'replayed':{k:len(v) for k,v in results.items()}}))
if __name__=='__main__':main()

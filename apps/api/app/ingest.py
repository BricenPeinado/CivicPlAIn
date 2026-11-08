"""Explicit acquisition, offline dry-run and reviewed atomic publication."""
import argparse
import json
from pathlib import Path

from app.ingestion.acquire import acquire
from app.ingestion.pipeline import stage, publish


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    acq=commands.add_parser('acquire',help='Fixed official HTTPS sources; writes new ignored evidence directory')
    acq.add_argument('--output',type=Path,required=True)
    acq.add_argument('--permit-since',required=True,help='Explicit YYYY-MM-DD permit issue lower bound')
    acq.add_argument('--permit-window-start')
    acq.add_argument('--permit-window-end')
    acq.add_argument('--permit-cap',type=int,default=20000)
    acq.add_argument('--base-acquisition',type=Path,help='Verified pinned non-permit source archive; explicit window only')
    for name in ['dry-run','publish']:
        sub=commands.add_parser(name)
        sub.add_argument('--acquisition',type=Path,required=True)
        sub.add_argument('--decisions',type=Path,help='Optional reviewed match decisions JSON')
        if name=='dry-run':
            sub.add_argument('--report',type=Path,required=True,help='New report path; never overwrites an earlier review')
        else:
            sub.add_argument('--database',type=Path,required=True)
            sub.add_argument('--approve-report',required=True)
            sub.add_argument('--allow-rejects',action='store_true')
    for name in ['intelligence-dry-run','intelligence-publish','permit-intelligence-dry-run','permit-intelligence-publish']:
        sub=commands.add_parser(name,help='Read-derived road association overlay on an existing immutable snapshot')
        sub.add_argument('--database',type=Path,required=True)
        sub.add_argument('--snapshot',required=True)
        sub.add_argument('--decisions',type=Path,help='Reviewed zero/one/many source-target decisions JSON list')
        if name.endswith('dry-run'):
            sub.add_argument('--report',type=Path,required=True)
            sub.add_argument('--review-bundle',type=Path,required=True,help='New ignored candidate evidence file; not an accepted decision')
        else:
            sub.add_argument('--approve-report',required=True)
    args=parser.parse_args()
    if args.command.startswith(('intelligence-','permit-intelligence-')):
        from app.core.municipal_repository import MunicipalRepository
        from app.core.intelligence_repository import IntelligenceRepository
        from app.services.road_intelligence import stage_overlay
        if args.command.startswith('permit-'):
            from app.services.permit_intelligence import stage_overlay
        staged=stage_overlay(MunicipalRepository(args.database),args.snapshot,
                             json.loads(args.decisions.read_text()) if args.decisions else [])
        if args.command.endswith('dry-run'):
            # Reserve both outputs without overwriting earlier review work.
            if args.report.resolve()==args.review_bundle.resolve() or args.report.exists() or args.review_bundle.exists():
                raise ValueError('Report and review bundle require distinct new paths')
            for path,value in [(args.report,staged['report']),(args.review_bundle,staged)]:
                path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('x') as output:
                    json.dump(value,output,indent=2);output.write('\n')
            result=staged['report']
        else:
            result=IntelligenceRepository(args.database).publish(staged,args.approve_report)
    elif args.command=='acquire':
        result=acquire(args.output,args.permit_since,args.permit_window_start,args.permit_window_end,args.permit_cap,args.base_acquisition)
    else:
        staged=stage(args.acquisition,json.loads(args.decisions.read_text()) if args.decisions else {})
        if args.command=='dry-run':
            args.report.parent.mkdir(parents=True,exist_ok=True)
            with args.report.open('x') as output:
                json.dump(staged['report'],output,indent=2)
                output.write('\n')
            result=staged['report']
        else:
            result=publish(args.database,staged,args.approve_report,args.allow_rejects)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()

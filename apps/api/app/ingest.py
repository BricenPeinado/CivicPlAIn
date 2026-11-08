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
    args=parser.parse_args()
    if args.command=='acquire':
        result=acquire(args.output,args.permit_since)
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

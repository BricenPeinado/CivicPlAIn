"""Run only with application writers stopped; never called on API startup."""
import argparse
import json
from pathlib import Path

from app.models.migrations import migrate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--backup',type=Path,required=True,help='New private backup file; never overwritten')
    parser.add_argument('--target-version',type=int,choices=[7,8,9,10,11,12],default=7)
    args=parser.parse_args()
    print(json.dumps(migrate(args.database,args.backup,target_version=args.target_version),sort_keys=True))


if __name__=='__main__':
    main()

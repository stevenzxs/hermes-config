"""Shared baseline-preserving revision policy (Android split codes included)."""
import argparse
import json
from pathlib import Path


def versions_for_revision(revision):
    if type(revision) is not int or revision < 1:
        raise ValueError('revision must be a positive integer')
    code = int(f'3049{revision}')
    if code * 10 + 3 > 2100000000:
        raise ValueError('Android ABI split versionCode exceeds platform limit')
    return dict(revision=revision, agent_baseline='0.23.1',
                android_baseline='4.0.0', agent_version=f'0.23.1+r{revision}',
                android_version=f'4.0.0+r{revision}', android_code=code,
                image_tag=f'0.23.1-r{revision}')


def next_revision(records, run_id):
    seen_runs, seen_revisions = set(), set()
    for record in records:
        versions_for_revision(record['revision'])
        if record['run_id'] in seen_runs or record['revision'] in seen_revisions:
            raise ValueError('duplicate revision ledger entry')
        seen_runs.add(record['run_id'])
        seen_revisions.add(record['revision'])
    for record in records:
        if record['run_id'] == run_id:
            return record['revision']
    return max(seen_revisions, default=0) + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', type=Path)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.ledger.read_text()) if args.ledger.exists() else []
    revision = next_revision(records, args.run_id)
    if not any(r['run_id'] == args.run_id for r in records):
        records.append(dict(run_id=args.run_id, revision=revision))
    args.ledger.write_text(json.dumps(records, indent=2) + '\n')
    args.output.write_text(json.dumps(versions_for_revision(revision), indent=2) + '\n')


if __name__ == '__main__':
    main()

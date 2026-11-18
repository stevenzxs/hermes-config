"""Persistent delivery checkpoints, not an automatic deployment executor."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import time

ROOT = Path('/opt/data/delivery-controller/tasks')
NEXT = {'prepared': {'building', 'failed'},
        'building': {'published', 'failed'},
        'published': {'deploying', 'failed'},
        'deploying': {'verified', 'failed'}, 'verified': set(), 'failed': set()}


def task_path(root, task_id):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', task_id):
        raise ValueError('Invalid task ID')
    return root / (task_id + '.json')


@contextmanager
def locked(root, task_id):
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = task_path(root, task_id)
    lock = path.with_suffix('.lock')
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield path
    finally:
        os.close(descriptor)
        lock.unlink()


def save(path, record):
    temp = path.with_suffix('.tmp')
    descriptor = os.open(temp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(record, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def create_task(root, task_id, request):
    if request.get('target') != '115.190.243.21':
        raise ValueError('Only the explicitly approved 115 target is supported')
    with locked(root, task_id) as path:
        if path.exists():
            record = json.loads(path.read_text())
            if record['request'] != request:
                raise ValueError('Task ID already belongs to a different request')
            return record
        record = {'task_id': task_id, 'request': request, 'state': 'prepared',
                  'history': [], 'created': int(time.time())}
        save(path, record)
        return record


def transition(root, task_id, state, evidence):
    with locked(root, task_id) as path:
        record = json.loads(path.read_text())
        if state not in NEXT[record['state']]:
            raise ValueError('Invalid state transition; do not repeat side effects')
        if state == 'building' and not isinstance(evidence.get('run_id'), int):
            raise ValueError('A dispatched Run ID is required')
        if state == 'published':
            valid = (evidence.get('run_conclusion') == 'success'
                     and evidence.get('artifacts_verified') is True
                     and re.fullmatch(r'sha256:[0-9a-f]{64}', evidence.get('digest', ''))
                     and all(re.fullmatch(r'[0-9a-f]{40}', evidence.get(k, ''))
                             for k in ['source_sha', 'config_sha', 'android_sha']))
            if not valid:
                raise ValueError('Verified publication evidence is required')
        if state == 'verified' and not all(evidence.get(k) is True for k in
                ['health', 'authentication', 'persistence', 'business']):
            raise ValueError('Runtime acceptance evidence is incomplete')
        record['history'].append({'from': record['state'], 'to': state,
                                  'time': int(time.time()), 'evidence': evidence})
        record['state'] = state
        save(path, record)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'status', 'transition'])
    parser.add_argument('task_id')
    parser.add_argument('--json', default='{}', help='Non-secret request/evidence only')
    parser.add_argument('--state', choices=list(NEXT))
    args = parser.parse_args()
    if args.action == 'status':
        result = json.loads(task_path(ROOT, args.task_id).read_text())
    elif args.action == 'create':
        result = create_task(ROOT, args.task_id, json.loads(args.json))
    else:
        result = transition(ROOT, args.task_id, args.state, json.loads(args.json))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

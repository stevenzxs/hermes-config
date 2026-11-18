"""Hermes-side orchestration for the joint release chain.

Schedules the reviewed hermes-config Actions workflow with fixed three-repository
SHAs, tracks the Run and records evidence through linux/delivery_task.py.
This tool never prints tokens and never repeats a dispatch for an uncertain
outcome: query the recorded Run ID first.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import delivery_task

GH = '/opt/data/delivery-controller/gh'
REPO = 'stevenzxs/hermes-config'
WORKFLOW = 'hermes-joint-release.yml'
TARGET = '115.190.243.21'
SEMVER = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
                    r'(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?')
SHA = re.compile(r'[0-9a-f]{40}')
SECRET_LIKE = re.compile(r'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|'
                         r'gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,})')


def validate_request(request):
    """Refuse drifted or malformed fixed inputs before anything is dispatched."""
    for key in ('source_sha', 'android_sha', 'config_sha'):
        if not SHA.fullmatch(str(request.get(key, ''))):
            raise ValueError(f'{key} must be a full lowercase commit SHA')
    if not SEMVER.fullmatch(str(request.get('version', ''))):
        raise ValueError('version must be a committed semantic versionName')
    code = request.get('android_code')
    previous = request.get('previous_android_code')
    if type(code) is not int or type(previous) is not int \
            or not previous < code <= 2100000000:
        raise ValueError('android_code must exceed previous_android_code')
    if request.get('target') != TARGET:
        raise ValueError(f'Only the explicitly approved {TARGET} target is supported')
    return request


def check_record_safe(record):
    text = json.dumps(record)
    if SECRET_LIKE.search(text):
        raise ValueError('Record appears to contain a token; refusing to handle')
    return record


def build_dispatch_args(request, ref='main'):
    return [GH, 'workflow', 'run', WORKFLOW, '--repo', REPO, '--ref', ref,
            '-f', f"source_sha={request['source_sha']}",
            '-f', f"android_sha={request['android_sha']}",
            '-f', f"version={request['version']}",
            '-f', f"android_code={request['android_code']}",
            '-f', f"previous_android_code={request['previous_android_code']}"]


def find_run_id(runs, config_sha):
    """Pick the dispatched Run by matching head SHA; never guess by time alone."""
    for run in runs:
        if run.get('headSha') == config_sha:
            return run['databaseId']
    raise RuntimeError('No Run found for the fixed config SHA; '
                       'list runs before dispatching again')


def run_gh(args, timeout=60):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"gh failed: {result.stderr.strip()[:200]}")
    return result.stdout


def load_record(task_id):
    path = delivery_task.task_path(delivery_task.ROOT, task_id)
    return check_record_safe(json.loads(path.read_text()))


def cmd_prepare(args):
    request = {'target': TARGET, 'source_sha': args.source_sha,
               'android_sha': args.android_sha, 'config_sha': args.config_sha,
               'version': args.version, 'android_code': args.android_code,
               'previous_android_code': args.previous_android_code}
    validate_request(request)
    record = delivery_task.create_task(delivery_task.ROOT, args.task_id, request)
    print(json.dumps(record, indent=2))


def cmd_dispatch(args):
    record = load_record(args.task_id)
    if record['state'] != 'prepared':
        raise SystemExit(f"Task state is {record['state']}; refusing to re-dispatch")
    request = validate_request(record['request'])
    run_gh(build_dispatch_args(request))
    deadline = time.time() + 120
    run_id = None
    while time.time() < deadline:
        time.sleep(10)
        out = run_gh([GH, 'run', 'list', '--workflow', WORKFLOW, '--repo', REPO,
                      '--limit', '10', '--json', 'databaseId,headSha,createdAt'])
        try:
            run_id = find_run_id(json.loads(out), request['config_sha'])
            break
        except RuntimeError:
            continue
    if run_id is None:
        raise SystemExit('Dispatch accepted but Run not visible yet; '
                         'query status later, do not dispatch again')
    record = delivery_task.transition(delivery_task.ROOT, args.task_id,
                                      'building', {'run_id': run_id})
    print(json.dumps(record, indent=2))


def cmd_status(args):
    record = load_record(args.task_id)
    history = record.get('history', [])
    if history:
        last = history[-1].get('evidence', {})
        run_id = last.get('run_id')
        if run_id:
            out = run_gh([GH, 'run', 'view', str(run_id), '--repo', REPO,
                          '--json', 'status,conclusion,url'])
            record['remote'] = json.loads(out)
    print(json.dumps(record, indent=2))


def cmd_verify(args):
    evidence = {'run_conclusion': args.run_conclusion,
                'artifacts_verified': args.artifacts_verified,
                'digest': args.digest, 'source_sha': args.source_sha,
                'config_sha': args.config_sha, 'android_sha': args.android_sha}
    record = delivery_task.transition(delivery_task.ROOT, args.task_id,
                                      'published', evidence)
    print(json.dumps(record, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'dispatch', 'status', 'verify'])
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--source-sha')
    parser.add_argument('--android-sha')
    parser.add_argument('--config-sha')
    parser.add_argument('--version')
    parser.add_argument('--android-code', type=int)
    parser.add_argument('--previous-android-code', type=int)
    parser.add_argument('--run-conclusion')
    parser.add_argument('--artifacts-verified', action='store_true')
    parser.add_argument('--digest')
    args = parser.parse_args()
    actions = {'prepare': cmd_prepare, 'dispatch': cmd_dispatch,
               'status': cmd_status, 'verify': cmd_verify}
    actions[args.action](args)


if __name__ == '__main__':
    main()

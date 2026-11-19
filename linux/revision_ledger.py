"""Append-only joint allocations with independent snapshots; never auto-bootstrap."""
import argparse
from contextlib import closing, contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time

from revision_versions import versions_for_revision

IDENTITY = ('hermes-joint:0.23.1:4.0.0:3049:v1',)
KEYS = {'repository', 'workflow', 'task_id', 'run_id', 'source_sha', 'android_sha', 'config_sha'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


@contextmanager
def exclusive(path):
    """OS lock released on process exit, unlike stale O_EXCL sentinel files."""
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        deadline = time.monotonic() + 30
        while True:
            try:
                stream.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise TimeoutError('Revision ledger lock is busy')
                time.sleep(0.02)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def validate_request(request):
    if set(request) != KEYS:
        raise ValueError('Exact immutable allocation request required')
    if request['repository'] != 'stevenzxs/hermes-config' or request['workflow'] != 'hermes-joint-release.yml':
        raise ValueError('Wrong allocation namespace')
    patterns = dict(run_id=r'[1-9][0-9]*', task_id=r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',
                    source_sha=r'[0-9a-f]{40}', android_sha=r'[0-9a-f]{40}', config_sha=r'[0-9a-f]{40}')
    for key, pattern in patterns.items():
        if not isinstance(request[key], str) or not re.fullmatch(pattern, request[key]):
            raise ValueError('Invalid allocation field: ' + key)


def connect(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError('Explicitly initialized persistent ledger required')
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=rw', uri=True, timeout=30)
    con.execute('PRAGMA synchronous=FULL')
    return con


def state(con):
    if con.execute('PRAGMA integrity_check').fetchone() != ('ok',):
        raise ValueError('Corrupt ledger')
    identity = con.execute('SELECT namespace,history_sha256 FROM identity').fetchall()
    if len(identity) != 1 or identity[0][0] != IDENTITY[0] or not re.fullmatch('[0-9a-f]{64}', identity[0][1]):
        raise ValueError('Ledger policy/namespace changed')
    rows = con.execute('SELECT run_id,revision,record FROM allocations ORDER BY revision').fetchall()
    for expected, (run, revision, payload) in enumerate(rows, 1):
        record = json.loads(payload)
        validate_request(record['request'])
        if revision != expected or record['request']['run_id'] != run or record['versions'] != versions_for_revision(expected):
            raise ValueError('Missing/corrupt allocation history')
    attempts = con.execute('SELECT run_id,attempt FROM attempts ORDER BY run_id,attempt').fetchall()
    if any(run not in {r[0] for r in rows} or type(attempt) is not int or attempt < 1 for run, attempt in attempts):
        raise ValueError('Invalid attempt history')
    return dict(identity=identity, allocations=rows, attempts=attempts)


def witness(backups):
    """Validate every immutable snapshot and hash-chain entry, not only the tip."""
    records = sorted(backups.glob('*.json'))
    if not records:
        raise ValueError('Independent backup witness missing')
    previous = ''
    latest = None
    for sequence, path in enumerate(records):
        if path.name != f'{sequence:08d}.json':
            raise ValueError('Incomplete backup witness history')
        entry = json.loads(path.read_text())
        snapshot = backups / f'{sequence:08d}.sqlite'
        if entry['previous'] != previous or not snapshot.is_file() or snapshot.is_symlink() or digest(snapshot.read_bytes()) != entry['backup_sha256']:
            raise ValueError('Independent backup witness mismatch')
        previous = digest(path.read_bytes())
        latest = entry
    if len(list(backups.glob('*.sqlite'))) != len(records):
        raise ValueError('Interrupted backup; explicit reconciliation required')
    return len(records) - 1, latest


def snapshot(con, backups, sequence):
    target = backups / f'{sequence:08d}.sqlite'
    if target.exists():
        raise ValueError('Backup sequence exists')
    with closing(sqlite3.connect(target)) as backup:
        con.backup(backup)
    os.chmod(target, 0o600)
    previous = digest((backups / f'{sequence - 1:08d}.json').read_bytes()) if sequence else ''
    payload = encode(dict(previous=previous, state_sha256=digest(encode(state(con))),
                          backup_sha256=digest(target.read_bytes())))
    with (backups / f'{sequence:08d}.json').open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    with target.open('r+b') as stream:
        os.fsync(stream.fileno())


def initialize(path, backups, *, history_sha256):
    if not re.fullmatch('[0-9a-f]{64}', history_sha256):
        raise ValueError('Reviewed historical inventory SHA256 required to initialize')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.resolve() == backups.resolve() or any(backups.iterdir()):
        raise ValueError('Empty independent backup directory required')
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    con = connect(path)
    try:
        con.executescript('''
        CREATE TABLE identity(namespace TEXT NOT NULL, history_sha256 TEXT NOT NULL);
        CREATE TABLE allocations(run_id TEXT PRIMARY KEY, revision INTEGER UNIQUE NOT NULL, record TEXT NOT NULL);
        CREATE TABLE attempts(run_id TEXT NOT NULL REFERENCES allocations(run_id), attempt INTEGER NOT NULL,
                              PRIMARY KEY(run_id,attempt));
        ''')
        for table in ('identity', 'allocations', 'attempts'):
            for action in ('UPDATE', 'DELETE'):
                con.execute(f"CREATE TRIGGER {table}_no_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'append only'); END")
        con.execute('INSERT INTO identity VALUES (?,?)', (*IDENTITY, history_sha256))
        con.commit()
        snapshot(con, backups, 0)
    finally:
        con.close()


def allocate(path, backups, request, *, attempt):
    validate_request(request)
    if type(attempt) is not int or attempt < 1:
        raise ValueError('Positive integer attempt required')
    if not path.is_file():
        raise ValueError('Explicitly initialized persistent ledger required')
    with exclusive(path.with_suffix('.lock')):
        con = connect(path)
        try:
            sequence, tip = witness(backups)
            current = state(con)
            if digest(encode(current)) != tip['state_sha256']:
                raise ValueError('Primary ledger stale or ahead of witness; explicit reconciliation required')
            rows = current['allocations']
            prior = next((json.loads(r[2]) for r in rows if r[0] == request['run_id']), None)
            if prior and prior['request'] != request:
                raise ValueError('Run reused with different immutable inputs')
            record = prior or dict(request=request, versions=versions_for_revision(len(rows) + 1))
            if prior and (request['run_id'], attempt) in {tuple(a) for a in current['attempts']}:
                return record
            with con:
                con.execute('BEGIN IMMEDIATE')
                if not prior:
                    con.execute('INSERT INTO allocations VALUES (?,?,?)',
                                (request['run_id'], record['versions']['revision'], encode(record).decode()))
                con.execute('INSERT INTO attempts VALUES (?,?)', (request['run_id'], attempt))
            # No allocation is returned until independent snapshot is durable.
            # Interruption after DB commit blocks future writes, never reuses N.
            snapshot(con, backups, sequence + 1)
            return record
        finally:
            con.close()


def recover(path, backups):
    """Explicit restore only; never overwrite a primary ahead of the witness."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with exclusive(path.with_suffix('.lock')):
        sequence, tip = witness(backups)
        source = backups / f'{sequence:08d}.sqlite'
        backup = connect(source)
        try:
            expected = state(backup)
        finally:
            backup.close()
        if digest(encode(expected)) != tip['state_sha256']:
            raise ValueError('Backup state witness mismatch')
        if path.exists():
            con = connect(path)
            try:
                current = state(con)
            finally:
                con.close()
            for key in ('allocations', 'attempts'):
                if not set(map(tuple, current[key])).issubset(set(map(tuple, expected[key]))):
                    raise ValueError('Primary ahead/diverged; manual reconciliation required, never rollback N')
            if current['identity'] != expected['identity']:
                raise ValueError('Recovery identity mismatch')
        staging = path.with_suffix('.recovery')
        with staging.open('xb') as stream:
            stream.write(source.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(staging, 0o600)
        staging.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['initialize', 'allocate', 'recover'])
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--backups', type=Path, required=True)
    parser.add_argument('--history-sha256')
    parser.add_argument('--request', type=Path)
    parser.add_argument('--attempt', type=int)
    args = parser.parse_args()
    if args.action == 'initialize':
        initialize(args.ledger, args.backups, history_sha256=args.history_sha256 or '')
    elif args.action == 'recover':
        recover(args.ledger, args.backups)
    else:
        print(json.dumps(allocate(args.ledger, args.backups, json.loads(args.request.read_text()), attempt=args.attempt)))


if __name__ == '__main__':
    main()

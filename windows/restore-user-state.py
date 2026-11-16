"""Restore user files only; never mutate the backup or reuse its runtimes."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3


EXCLUDED = {'bin', 'installs', 'runtime', 'tools', 'locks', 'cache',
            'source-checks', 'plugin-update-checks', 'gateway-service',
            'terminal-sessions', 'processes.json', 'spawn-ledger.json',
            'SingletonCookie', 'SingletonLock', 'SingletonSocket'}


def ignored(directory, names):
    return [name for name in names if name in EXCLUDED
            or name.endswith(('.lock', '.pid', '.db-shm'))]


def restore(backup, target):
    backup, target = Path(backup).resolve(), Path(target).resolve()
    if backup == target or backup in target.parents or target in backup.parents:
        raise ValueError('Backup and destination must be disjoint')
    for name in ('home', 'workspace'):
        if (target / name).exists():
            raise ValueError(f'Destination {name} already exists')
    for name in ('home', 'workspace'):
        source = backup / name
        for directory, dirs, files in os.walk(source, followlinks=False):
            excluded = set(ignored(directory, dirs + files)) if name == 'home' else set()
            dirs[:] = [entry for entry in dirs if entry not in excluded]
            for entry in dirs + [entry for entry in files if entry not in excluded]:
                path = Path(directory) / entry
                if path.is_symlink() or path.is_junction():
                    raise ValueError('Backup contains links; review before copying')
        shutil.copytree(source, target / name, ignore=ignored if name == 'home' else None)
    results = {}
    for database in (target / 'home').rglob('*.db'):
        with closing(sqlite3.connect(database)) as connection:
            status = connection.execute('PRAGMA quick_check').fetchall()
            if status != [('ok',)]:
                raise RuntimeError(f'Database check failed: {database.name}')
            connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        results[database.relative_to(target).as_posix()] = 'ok'
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup')
    parser.add_argument('target')
    args = parser.parse_args()
    print(json.dumps(restore(args.backup, args.target), indent=2))

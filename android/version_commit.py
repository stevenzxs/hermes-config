"""Deterministic joint-release version commit for the Android checkout.

Rewrites only the pubspec.yaml version line and commits with fixed identity and
the parent commit's timestamp, so the resulting commit SHA is a pure function of
(source commit, version, android_code). Auditors can reproduce the SHA without
needing the ephemeral runner workspace.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'linux'))
from revision_versions import versions_for_revision  # noqa: E402

AUTHOR = ('Hermes Joint Release', 'joint-release@stevenzxs.invalid')
VERSION_LINE = re.compile(r'^version:[ \t]*\S+[ \t]*$', re.MULTILINE)


def git(root, *args, env=None):
    merged = dict(os.environ)
    if env:
        merged.update(env)
    return subprocess.check_output(['git', '-C', str(root)] + list(args),
                                   text=True, env=env or None).strip()


def validate(version, android_code):
    if type(android_code) is not int or not re.fullmatch(r'4\.0\.0\+r[1-9][0-9]*', version or ''):
        raise ValueError('Version must be 4.0.0+rN and code an integer')
    revision = int(version.rsplit('r', 1)[1])
    expected = versions_for_revision(revision)
    if expected['android_version'] != version or expected['android_code'] != android_code:
        raise ValueError('Version/code do not match the ledger revision mapping')
    return revision


def create(root, version, android_code):
    root = Path(root)
    revision = validate(version, android_code)
    if git(root, 'status', '--porcelain'):
        raise ValueError('Android checkout must be clean')
    parent = git(root, 'rev-parse', 'HEAD')
    if git(root, 'log', '-1', '--format=%an') == AUTHOR[0]:
        raise ValueError('HEAD is already a joint version commit')
    pubspec = root / 'pubspec.yaml'
    text = pubspec.read_text()
    base = version.split('+', 1)[0]
    replacement = f'version: {base}+{android_code}'
    if replacement in text:
        raise ValueError('Checkout already carries this version')
    if len(VERSION_LINE.findall(text)) != 1:
        raise ValueError('pubspec.yaml must contain exactly one version line')
    pubspec.write_text(VERSION_LINE.sub(replacement, text, count=1))
    commit_date = git(root, 'show', '-s', '--format=%cI', parent)
    env = {'GIT_AUTHOR_NAME': AUTHOR[0], 'GIT_AUTHOR_EMAIL': AUTHOR[1],
           'GIT_COMMITTER_NAME': AUTHOR[0], 'GIT_COMMITTER_EMAIL': AUTHOR[1],
           'GIT_AUTHOR_DATE': commit_date, 'GIT_COMMITTER_DATE': commit_date}
    git(root, 'add', 'pubspec.yaml')
    git(root, 'commit', '-q', '-m',
        f'chore(release): joint revision r{revision} ({version}+{android_code})', env=env)
    commit = git(root, 'rev-parse', 'HEAD')
    return dict(commit=commit, parent=parent, version=version,
                android_code=android_code, revision=revision)


def main():
    if len(sys.argv) != 4:
        raise SystemExit('Use: version_commit.py ANDROID_DIR VERSION ANDROID_CODE')
    record = create(Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()

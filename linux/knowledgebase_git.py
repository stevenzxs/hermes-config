"""Repository-scoped Git credential helper and branch/PR submission entrypoint."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

REPO = 'stevenzxs/knowledgebase'
ROOT = Path('/opt/data/workspace/knowledgebase')
AUTH = Path('/run/knowledgebase-auth')


def allowed_credential(fields):
    return (fields.get('protocol') == 'https' and fields.get('host') == 'github.com'
            and fields.get('path', '').removesuffix('.git') == REPO)


def safe_branch(branch):
    return bool(re.fullmatch(r'hermes/[a-zA-Z0-9][a-zA-Z0-9._/-]*', branch)
                and '..' not in branch and not branch.endswith(('/', '.lock')))


def token():
    path = AUTH / 'token'
    if not path.is_file():
        raise ValueError('Repository-scoped token not provisioned')
    if os.name != 'nt' and path.stat().st_mode & 0o077:
        raise ValueError('Token permissions must be 600')
    value = path.read_text().strip()
    if not value or any(c.isspace() for c in value):
        raise ValueError('Invalid token file')
    return value


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def check_origin():
    expected = 'https://github.com/' + REPO + '.git'
    if git('remote', 'get-url', 'origin') != expected or git('remote', 'get-url', '--push', 'origin') != expected:
        raise ValueError('Unexpected remote; refusing credential use')


def api(path, key, body=None):
    request = urllib.request.Request(
        'https://api.github.com/repos/' + REPO + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': 'Bearer ' + key, 'Accept': 'application/vnd.github+json',
                 'Content-Type': 'application/json', 'User-Agent': 'hermes-knowledgebase',
                 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def submit(title):
    check_origin()
    branch = git('branch', '--show-current')
    if not safe_branch(branch):
        raise ValueError('Only hermes/<task> branches may be submitted')
    if git('status', '--porcelain'):
        raise ValueError('Commit reviewed changes first; working tree must be clean')
    proof = json.loads((AUTH / 'protection-verified.json').read_text())
    if (proof.get('repository') != REPO or proof.get('verified') is not True
            or not proof.get('evidence') or not proof.get('verifiedAt')):
        raise ValueError('Server-side branch protection/scope verification required')
    key = token()
    metadata = api('', key)
    base = metadata['default_branch']
    # Never force or delete; the explicitly named ref cannot target the default branch.
    subprocess.run(['git', '-C', str(ROOT), 'push', 'origin', f'HEAD:refs/heads/{branch}'], check=True)
    from urllib.parse import urlencode
    prs = api('/pulls?' + urlencode({'state': 'open', 'head': 'stevenzxs:' + branch, 'base': base}), key)
    pr = prs[0] if prs else api('/pulls', key, {'title': title, 'head': branch, 'base': base,
                                             'body': 'Hermes knowledgebase proposal. Human review required; no auto-merge.'})
    print(pr['html_url'])


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == 'credential':
        if sys.argv[2] != 'get':
            return
        fields = dict(line.rstrip('\n').split('=', 1) for line in sys.stdin if '=' in line)
        if allowed_credential(fields):
            print('username=x-access-token\npassword=' + token())
        return
    if sys.argv[1:] == ['status']:
        check_origin()
        print(json.dumps({'repository': REPO, 'branch': git('branch', '--show-current'),
                          'commit': git('rev-parse', 'HEAD'), 'dirty': bool(git('status', '--porcelain')),
                          'token_provisioned': (AUTH / 'token').is_file(),
                          'protection_attestation_present': (AUTH / 'protection-verified.json').is_file()}))
    elif len(sys.argv) == 3 and sys.argv[1] == 'submit':
        submit(sys.argv[2])
    else:
        raise ValueError('Use status or submit "PR title"')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # HTTP bodies, subprocess output and credential-bearing errors are never echoed.
        print('Knowledgebase operation blocked: ' + type(exc).__name__, file=sys.stderr)
        sys.exit(1)

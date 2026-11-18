"""Read-only controller GitHub admission; never prints credential values."""
import json
import subprocess

GH = '/opt/data/delivery-controller/gh'
REPOSITORIES = ('hermes-agent', 'hermes-config', 'hermes-android')
SIGNING = {'KEYSTORE_BASE64', 'STORE_PASSWORD', 'KEY_PASSWORD', 'KEY_ALIAS'}


def admit_repository(metadata, name):
    if name not in REPOSITORIES:
        raise ValueError('Repository is not approved')
    if metadata.get('full_name') != 'stevenzxs/' + name:
        raise ValueError('Unexpected repository identity')
    if metadata.get('permissions', {}).get('push') is not True:
        raise ValueError('Repository push permission is missing')


def signing_ready(names):
    return SIGNING.issubset(set(names))


def api(path):
    result = subprocess.run([GH, 'api', path], capture_output=True, text=True,
                            timeout=30)
    if result.returncode:
        raise RuntimeError('GitHub API preflight failed; inspect authentication or connectivity')
    return json.loads(result.stdout)


def main():
    user = api('user')
    if user.get('login') != 'stevenzxs':
        raise ValueError('Unexpected GitHub account')
    admitted = []
    for name in REPOSITORIES:
        metadata = api('repos/stevenzxs/' + name)
        admit_repository(metadata, name)
        admitted.append({'repository': metadata['full_name'],
                         'default_branch': metadata['default_branch'], 'push': True})
    secrets = api('repos/stevenzxs/hermes-config/actions/secrets?per_page=100')
    ready = signing_ready(item['name'] for item in secrets['secrets'])
    print(json.dumps({'account': user['login'], 'repositories': admitted,
                      'android_signing_names_present': ready,
                      'signing_values_verified': False,
                      'git_transport_verified': False}, indent=2))
    if not ready:
        raise ValueError('Android signing prerequisites are missing')


if __name__ == '__main__':
    main()

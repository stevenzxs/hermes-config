"""Validate native unpacked identity without assuming a stable executable name."""
import json
from pathlib import Path
import sys


def inspect_artifact(root, commit):
    root = Path(root).resolve()
    payload = root / 'resources/agent-payload'
    stamp = json.loads((root / 'resources/install-stamp.json').read_text(encoding='utf-8'))
    manifest = json.loads((payload / 'manifest.json').read_text(encoding='utf-8'))
    if stamp['commit'] != commit or manifest['ref'] != commit or stamp['dirty']:
        raise ValueError('Artifact does not match the clean admitted commit')
    if stamp['payload'] != 'bundled':
        raise ValueError('A self-contained bundled payload is required')
    command = stamp['runtime']['commands']['hermes']
    cli = (payload / command).resolve()
    if not cli.is_relative_to(payload.resolve()) or not cli.is_file():
        raise ValueError('CLI command escapes payload or is missing')
    if manifest['runtime']['commands']['hermes'] != command:
        raise ValueError('Payload and desktop CLI identities differ')
    executables = list(root.glob('*.exe'))
    if len(executables) != 1:
        raise ValueError('Expected exactly one desktop executable')
    return {'commit': commit, 'desktop': executables[0].name,
            'cli': cli.relative_to(root).as_posix(), 'displayVersion': stamp.get('displayVersion')}


if __name__ == '__main__':
    print(json.dumps(inspect_artifact(sys.argv[1], sys.argv[2])))

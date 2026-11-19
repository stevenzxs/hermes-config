"""Explicit offline delivery node; never invoked by the normal registry workflow."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

SOURCE = None  # Read from build-record.json, not hardcoded
REGISTRY = 'ghcr.io/stevenzxs/hermes-agent'
PAYLOAD = {'image.tar.gz', 'install-offline.sh', 'upgrade-offline.sh', 'compose.yml', 'offline_bundle.py', 'README.md'}
FILES = PAYLOAD | {'manifest.json'}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''): h.update(data)
    return h.hexdigest()


def write_checksums(root):
    (root / 'SHA256SUMS').write_text(''.join(f'{digest(root / n)}  {n}\n' for n in sorted(FILES)))


def verify(root):
    entries = {}
    for line in (root / 'SHA256SUMS').read_text().splitlines():
        sha, name = line.split('  ', 1)
        if name not in FILES or name in entries or not re.fullmatch('[0-9a-f]{64}', sha):
            raise ValueError('Invalid checksum entry')
        if (root / name).is_symlink() or digest(root / name) != sha:
            raise ValueError('Checksum mismatch: ' + name)
        entries[name] = sha
    if set(entries) != FILES: raise ValueError('Incomplete checksum coverage')
    m = json.loads((root / 'manifest.json').read_text())
    if not re.fullmatch('sha256:[0-9a-f]{64}', m['imageId']): raise ValueError('Invalid image ID')
    if not re.fullmatch(re.escape(REGISTRY) + '@sha256:[0-9a-f]{64}', m['registryImage']):
        raise ValueError('Invalid registry identity')
    for k in ('buildConfigCommit', 'packagingConfigCommit'):
        if not re.fullmatch('[0-9a-f]{40}', m[k]): raise ValueError('Invalid config identity')
    if not re.fullmatch('[0-9a-f]{40}', m['sourceCommit']): raise ValueError('Invalid source commit')
    if m['platform'] != 'linux/amd64': raise ValueError('Wrong platform')
    if not re.fullmatch('hermes-offline:[a-z0-9-]+', m['localTag']): raise ValueError('Invalid local tag')
    return m


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def archive_image_id(path):
    with tarfile.open(path, 'r:gz') as tar:
        manifest = json.load(tar.extractfile('manifest.json'))
        if len(manifest) != 1: raise ValueError('Expected one exported image')
        name = manifest[0]['Config']
        data = tar.extractfile(name).read()
        sha = hashlib.sha256(data).hexdigest()
        if sha not in name: raise ValueError('Exported config digest mismatch')
        return 'sha256:' + sha


def pack(delivery, root):
    if root.exists() or Path(str(root) + '.tar').exists(): raise ValueError('Output exists')
    repo = Path(__file__).resolve().parent.parent
    if output('git', '-C', str(repo), 'status', '--porcelain'): raise ValueError('Config must be clean')
    record = json.loads((delivery / 'build-record.json').read_text())
    source = record['sourceCommit']
    if not re.fullmatch(r'[0-9a-f]{40}', source): raise ValueError('Invalid source commit')
    smoke = json.loads((delivery / 'gateway-smoke.json').read_text())
    if smoke != dict(health=200, unauthenticated=401, wrong_token=401, authenticated=200):
        raise ValueError('Missing gateway acceptance')
    if 'Internal source identity verified' not in (delivery / 'identity-check.log').read_text():
        raise ValueError('Missing identity acceptance')
    registry = (delivery / 'published-image.txt').read_text().strip()
    if not re.fullmatch(re.escape(REGISTRY) + '@sha256:[0-9a-f]{64}', registry):
        raise ValueError('Invalid published registry identity')
    subprocess.run(['docker', 'pull', '--platform', 'linux/amd64', registry], check=True)
    inspect = json.loads(output('docker', 'image', 'inspect', registry))[0]
    if registry not in inspect['RepoDigests']: raise ValueError('Published digest not in local image')
    labels = inspect['Config']['Labels']
    if labels['org.opencontainers.image.revision'] != source: raise ValueError('Wrong source label')
    if labels['io.stevenzxs.hermes.config-revision'] != record['configCommit']: raise ValueError('Wrong build config')
    if inspect['Os'] != 'linux' or inspect['Architecture'] != 'amd64': raise ValueError('Wrong platform')
    root.mkdir(parents=True)
    tag = 'hermes-offline:src-' + source[:12] + '-cfg-' + record['configCommit'][:12]
    subprocess.run(['docker', 'tag', inspect['Id'], tag], check=True)
    with (root / 'image.tar.gz').open('wb') as target:
        proc = subprocess.Popen(['docker', 'save', tag], stdout=subprocess.PIPE)
        try:
            with gzip.GzipFile(fileobj=target, mode='wb', compresslevel=1, mtime=0) as z:
                shutil.copyfileobj(proc.stdout, z, 1024 * 1024)
        finally:
            proc.stdout.close()
        if proc.wait() != 0: raise ValueError('docker save failed')
    for name, src in [('install-offline.sh', 'install-offline.sh'), ('upgrade-offline.sh', 'upgrade-offline.sh'),
                      ('compose.yml', 'compose.yml'), ('offline_bundle.py', 'offline_bundle.py'), ('README.md', 'OFFLINE.md')]:
        shutil.copyfile(repo / 'linux' / src, root / name)
    m = dict(sourceCommit=source, buildConfigCommit=record['configCommit'],
             packagingConfigCommit=output('git', '-C', str(repo), 'rev-parse', 'HEAD'),
             registryImage=registry, imageId=archive_image_id(root / 'image.tar.gz'),
             platform='linux/amd64', localTag=tag)
    (root / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n')
    write_checksums(root); verify(root)
    archive = Path(str(root) + '.tar')
    with tarfile.open(archive, 'w') as tar:
        for name in sorted(FILES | {'SHA256SUMS'}): tar.add(root / name, arcname=name)
    Path(str(archive) + '.sha256').write_text(digest(archive) + '  ' + archive.name + '\n')
    print('Bundle:', archive, '\nSHA256:', digest(archive))


if __name__ == '__main__':
    if sys.argv[1] == 'verify':
        verify(Path(sys.argv[2])); print('Bundle checksums and manifest verified')
    elif sys.argv[1] == 'pack': pack(Path(sys.argv[2]), Path(sys.argv[3]))
    else: raise SystemExit('Use pack DELIVERY OUTPUT or verify DIRECTORY')

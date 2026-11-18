"""Install verified GitHub CLI in the controller's persistent data volume."""
import hashlib
import io
import os
from pathlib import Path
import subprocess
import tarfile
import urllib.request

VERSION = '2.105.0'
SHA256 = '79e7ab5db738c48777b696e374f8b428f0647debfb424f44d2f426370407fe2f'
ROOT = Path('/opt/data/delivery-controller')


def main():
    os.umask(0o077)
    ROOT.mkdir(mode=0o700, exist_ok=True)
    binary = ROOT / ('gh-' + VERSION)
    if not binary.exists():
        url = (f'https://github.com/cli/cli/releases/download/v{VERSION}/'
               f'gh_{VERSION}_linux_amd64.tar.gz')
        with urllib.request.urlopen(url, timeout=90) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != SHA256:
            raise ValueError('GitHub CLI archive checksum mismatch')
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            member = archive.extractfile(f'gh_{VERSION}_linux_amd64/bin/gh')
            if member is None:
                raise ValueError('Missing CLI binary')
            content = member.read()
        temporary = binary.with_suffix('.tmp')
        temporary.write_bytes(content)
        temporary.chmod(0o700)
        temporary.replace(binary)
    auth = ROOT / 'auth'
    auth.mkdir(mode=0o700, exist_ok=True)
    wrapper = ROOT / 'gh'
    wrapper.write_text('#!/bin/sh\n'
                       'export GH_CONFIG_DIR=/opt/data/delivery-controller/auth\n'
                       'export GH_HOST=github.com\n'
                       f'exec /opt/data/delivery-controller/gh-{VERSION} "$@"\n')
    wrapper.chmod(0o700)
    subprocess.run([str(wrapper), '--version'], check=True)


if __name__ == '__main__':
    main()

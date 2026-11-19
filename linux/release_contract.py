"""Validate fixed inputs before joint release; never rewrites product versions."""
import argparse
import json
from pathlib import Path
import re

SEMVER = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
                    r'(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?'
                    r'(?:\+r[1-9][0-9]*)?')
BASELINE_VERSION = '4.0.0'
BASELINE_CODE = 3048


def validate_release(request, pubspec, previous_android_code=BASELINE_CODE):
    version = request.get('version', '')
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise ValueError('Invalid unified release version')
    for key in ['source_sha', 'config_sha', 'android_sha']:
        value = request.get(key)
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}', value):
            raise ValueError('Full fixed source/config SHAs are required')
    code = request.get('android_code')
    if type(code) is not int or not previous_android_code < code <= 2100000000:
        raise ValueError('Android versionCode must increase within platform range')
    # The input android_sha is the reviewed base commit; the allocated version is
    # applied by the deterministic version commit during the build. The base
    # commit must still carry the untouched baseline declaration.
    versions = re.findall(r'^version:[ \t]*(\S+)[ \t]*$', pubspec, re.MULTILINE)
    if versions != [f'{BASELINE_VERSION}+{previous_android_code + 1}']:
        raise ValueError('Android base commit must carry the untouched baseline version')
    return request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('android_source', type=Path)
    parser.add_argument('--previous-android-code', type=int, default=BASELINE_CODE,
                        help='Published baseline floor; ledger allocations derive codes above it')
    args = parser.parse_args()
    request = json.loads(args.request.read_text())
    validate_release(request, (args.android_source / 'pubspec.yaml').read_text(),
                     args.previous_android_code)
    print('Unified version and fixed release inputs admitted; not a build result')


if __name__ == '__main__':
    main()

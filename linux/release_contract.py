"""Validate fixed inputs before joint release; never rewrites product versions."""
import argparse
import json
from pathlib import Path
import re


def validate_release(request, pubspec, previous_android_code=3048):
    version = request.get('version', '')
    if not isinstance(version, str) or not re.fullmatch(
            r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
            r'(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?', version):
        raise ValueError('Invalid unified release version')
    for key in ['source_sha', 'config_sha', 'android_sha']:
        value = request.get(key)
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}', value):
            raise ValueError('Full fixed source/config SHAs are required')
    code = request.get('android_code')
    if type(code) is not int or not previous_android_code < code <= 2100000000:
        raise ValueError('Android versionCode must increase within platform range')
    versions = re.findall(r'^version:[ \t]*(\S+)[ \t]*$', pubspec, re.MULTILINE)
    if versions != [f'{version}+{code}']:
        raise ValueError('Commit the matching Android version before dispatch')
    return request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('android_source', type=Path)
    parser.add_argument('--previous-android-code', type=int, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_text())
    validate_release(request, (args.android_source / 'pubspec.yaml').read_text(),
                     args.previous_android_code)
    print('Unified version and fixed release inputs admitted; not a build result')


if __name__ == '__main__':
    main()

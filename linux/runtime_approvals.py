#!/usr/bin/env python3
"""Check/apply the explicitly approved 150 policy, never copy full runtime config."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

try:
    # The deployed Hermes image owns its parser and duplicate-key policy.
    sys.path.append('/opt/hermes')
    from hermes_yaml import safe_load as load_yaml
except ImportError:
    import yaml

    class UniqueLoader(yaml.SafeLoader):
        """Reject ambiguous duplicate keys in local PyYAML validation too."""

    def unique_mapping(loader, node):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node)
            if key in result:
                raise ValueError('duplicate YAML key')
            result[key] = loader.construct_object(value_node)
        return result

    UniqueLoader.add_constructor('tag:yaml.org,2002:map', unique_mapping)

    def load_yaml(raw):
        return yaml.load(raw, Loader=UniqueLoader)


def read_policy(path):
    policy = json.loads(path.read_text(encoding='utf-8'))
    if (policy.get('instance') != '150.158.83.70'
            or policy.get('profile_home') != '/opt/data'
            or policy.get('approvals') != {'mode': 'smart', 'cron_mode': 'approve'}):
        raise ValueError('unexpected instance policy')
    return policy['approvals']


def candidate(raw, desired):
    config = load_yaml(raw.decode('utf-8'))
    if 'approvals' not in config:
        # Current 150 uses the merged defaults (smart/deny), not an explicit
        # mapping. Materialize only this approved override, preserving the file.
        output = raw + b'\napprovals:\n  mode: smart\n  cron_mode: approve\n'
        expected = dict(config, approvals=desired)
        if load_yaml(output.decode('utf-8')) != expected:
            raise ValueError('cannot append approvals safely')
        return output
    approvals = config.get('approvals', {})
    if approvals.get('mode') != 'smart' or approvals.get('cron_mode') not in ('deny', 'approve'):
        raise ValueError('expected existing smart mode and explicit deny/approve cron mode')
    if all(approvals.get(k) == v for k, v in desired.items()):
        return raw
    # Preserve comments, secrets, encoding and all unrelated bytes. Refuse unusual
    # inline/anchored syntax rather than reserializing the entire runtime file.
    block = re.search(rb'^approvals:[ \t]*\r?\n(?:[ \t]+[^\n]*\n|[ \t]*\r?\n|#[^\n]*\n)*', raw, re.M)
    if not block:
        raise ValueError('expected block-style approvals mapping')
    pattern = rb'(?m)^([ \t]+cron_mode:[ \t]*)deny(?=[ \t]*(?:#|\r?$))'
    updated, count = re.subn(pattern, rb'\1approve', block.group())
    if count != 1:
        raise ValueError('expected one plain cron_mode field')
    output = raw[:block.start()] + updated + raw[block.end():]
    parsed = load_yaml(output.decode('utf-8'))
    expected = load_yaml(raw.decode('utf-8'))
    expected['approvals'].update(desired)
    if parsed != expected:
        raise ValueError('unexpected configuration difference')
    return output


def apply_policy(path, policy, apply=False):
    if path.is_symlink() or not path.is_file():
        raise ValueError('expected regular non-symlink config file')
    info = path.stat()
    raw = path.read_bytes()
    output = candidate(raw, read_policy(policy))
    report = {'mode': 'smart', 'cron_mode': 'approve', 'matches': output == raw,
              'sha256': hashlib.sha256(raw).hexdigest(), 'changed': False}
    if output == raw or not apply:
        return report
    backup = path.with_name(path.name + '.before-cron-' +
                            datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
    fd, temporary = tempfile.mkstemp(prefix='.approvals-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(output)
            f.flush()
            os.fsync(f.fileno())
        if hasattr(os, 'chown'):
            os.chown(temporary, info.st_uid, info.st_gid)
        os.chmod(temporary, stat.S_IMODE(info.st_mode))
        if path.is_symlink() or path.stat().st_ino != info.st_ino or path.read_bytes() != raw:
            raise ValueError('concurrent config change; refusing replacement')
        fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
        if path.read_bytes() != output:
            raise ValueError('readback mismatch; backup retained')
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    report.update(matches=True, changed=True, backup=str(backup),
                  sha256=hashlib.sha256(output).hexdigest())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--policy', type=Path, required=True)
    parser.add_argument('--apply', action='store_true', help='requires explicit operator approval')
    args = parser.parse_args()
    try:
        result = apply_policy(args.config, args.policy, args.apply)
    except Exception:
        # YAML errors can contain credentials from the source line: never echo them.
        print('Policy check/apply refused; inspect config privately. No secrets logged.')
        return 2
    print(json.dumps(result))
    return 0 if result['matches'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

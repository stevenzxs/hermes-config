"""Materialize an authorized Android key on an ephemeral runner, fail closed."""
import base64
import os
from pathlib import Path
import subprocess
import sys

EXPECTED_CERT = '475baf431b16d050c8f658ac838783b273f7c10bba06ed1d16bb0a4239f592fb'
REQUIRED = ('KEYSTORE_BASE64', 'STORE_PASSWORD', 'KEY_PASSWORD', 'KEY_ALIAS')


def prepare(source, temporary, env):
    if any(not env.get(name) for name in REQUIRED):
        raise ValueError('All four release signing secrets are required; no debug fallback')
    source, temporary = Path(source), Path(temporary)
    key, properties = temporary / 'hermes-android-release.keystore', source / 'key.properties'
    if key.exists() or properties.exists():
        raise ValueError('Signing files already exist')
    for name in REQUIRED[1:]:
        if any(char in env[name] for char in '\r\n\x00') or not env[name].isascii():
            raise ValueError('Signing values must be single-line Java property values')
    data = base64.b64decode(env['KEYSTORE_BASE64'], validate=True)
    if not data:
        raise ValueError('Empty signing keystore')
    try:
        descriptor = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
        command = ['keytool', '-exportcert', '-keystore', str(key), '-alias', env['KEY_ALIAS'],
                   '-storepass:env', 'STORE_PASSWORD']
        result = subprocess.run(command, env=env, capture_output=True, check=True)
        import hashlib
        if hashlib.sha256(result.stdout).hexdigest() != EXPECTED_CERT:
            raise ValueError('Signing certificate does not match admitted production identity')
        def escaped(value):
            return ''.join('\\u%04x' % ord(c) if not c.isascii() or c in '\\:=#! ' else c for c in value)
        values = {'storeFile': key.as_posix(), 'storePassword': env['STORE_PASSWORD'],
                  'keyPassword': env['KEY_PASSWORD'], 'keyAlias': env['KEY_ALIAS']}
        properties.write_text(''.join(k + '=' + escaped(v) + '\n' for k, v in values.items()), encoding='ascii')
    except Exception:
        key.unlink(missing_ok=True)
        properties.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    try:
        prepare(sys.argv[1], sys.argv[2], os.environ.copy())
        print('Authorized production signing identity verified')
    except (ValueError, OSError, subprocess.SubprocessError):
        sys.exit('Release signing preparation failed; missing/invalid credentials or certificate mismatch')

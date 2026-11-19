import unittest
from release_contract import validate_release


class ReleaseContractTests(unittest.TestCase):
    def request(self):
        return dict(version='0.23.1+r2', android_code=30492,
                    source_sha='a'*40, config_sha='b'*40, android_sha='c'*40)

    def test_requires_untouched_baseline_pubspec(self):
        request = self.request()
        validate_release(request, 'version: 4.0.0+3049\n')
        with self.assertRaises(ValueError):
            validate_release(request, 'version: 4.0.0+r2+30492\n')
        with self.assertRaises(ValueError):
            validate_release(request, 'version: 4.0.0+3048\n')

    def test_accepts_ledger_revision_version(self):
        validate_release(self.request(), 'version: 4.0.0+3049\n')
        validate_release(dict(self.request(), version='0.23.1'), 'version: 4.0.0+3049\n')

    def test_rejects_floating_source_and_invalid_version(self):
        for change in [dict(source_sha='main'), dict(version='x; echo bad'),
                       dict(version='0.23.1+rc2'), dict(android_code=True),
                       dict(android_code=3048)]:
            with self.assertRaises(ValueError):
                validate_release(dict(self.request(), **change),
                                 'version: 4.0.0+3049\n')


if __name__ == '__main__':
    unittest.main()

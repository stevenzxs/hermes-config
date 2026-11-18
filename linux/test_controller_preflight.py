import unittest

from controller_preflight import admit_repository, signing_ready


class PreflightTests(unittest.TestCase):
    def test_repository_requires_intended_owner_and_push(self):
        admit_repository({'full_name': 'stevenzxs/hermes-config',
                          'permissions': {'push': True}}, 'hermes-config')
        for metadata in [
            {'full_name': 'other/hermes-config', 'permissions': {'push': True}},
            {'full_name': 'stevenzxs/hermes-config', 'permissions': {'push': False}},
        ]:
            with self.assertRaises(ValueError):
                admit_repository(metadata, 'hermes-config')

    def test_signing_requires_all_four_names(self):
        names = ['KEYSTORE_BASE64', 'STORE_PASSWORD', 'KEY_PASSWORD', 'KEY_ALIAS']
        self.assertTrue(signing_ready(names))
        self.assertFalse(signing_ready(names[:-1]))


if __name__ == '__main__':
    unittest.main()

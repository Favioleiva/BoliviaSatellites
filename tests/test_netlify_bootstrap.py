"""Failure-mode checks for pinned Release restoration; no network or publishing."""
from pathlib import Path
import copy
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_netlify import release_tag, validate_assets


class ReleasePreflight(unittest.TestCase):
    def setUp(self):
        self.base = 'https://github.com/Favioleiva/BoliviaSatellites/releases/download/v1.0.0'
        self.expected = [{'name': 'data.zip', 'bytes': 123, 'sha256': 'a' * 64}]
        self.release = {'draft': False, 'published_at': '2026-11-24T00:00:00Z', 'assets': [
            {'name': 'data.zip', 'state': 'uploaded', 'size': 123,
             'digest': 'sha256:' + 'a' * 64, 'browser_download_url': self.base + '/data.zip'}]}

    def test_missing_or_mutable_tag_rejected(self):
        for tag in [None, '', 'latest', 'LATEST', '../other', 'v1?token=x']:
            with self.subTest(tag=tag), self.assertRaises(ValueError):release_tag(tag)
        self.assertEqual(release_tag('v0.1.0-c05-review.1'), 'v0.1.0-c05-review.1')

    def test_matching_release(self):
        validate_assets(self.release, self.expected, self.base)

    def test_absent_and_draft_assets(self):
        for changes in [{'draft': True}, {'published_at': None}, {'assets': []}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_assets({**self.release, **changes}, self.expected, self.base)

    def test_mixed_or_corrupt_assets(self):
        for field, value in [('state', 'new'), ('size', 124), ('digest', 'sha256:' + 'b' * 64), ('browser_download_url', 'https://example.invalid/data.zip')]:
            release = copy.deepcopy(self.release);release['assets'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):validate_assets(release, self.expected, self.base)


if __name__ == '__main__':unittest.main()

"""Real pinned metadata/art import and read-only presentation compatibility."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
IOS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(IOS / 'content_tools'), str(IOS / 'prototype')]
from import_content import (DEFAULT_OUTPUT, DEFAULT_SOURCE, build_catalog, import_content,
                            load_lock, sha, verify_bundle)
from demo_data import prepare
from summon_service import SummonService


class UnitContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch = IOS / '.local'
        cls.temp = tempfile.TemporaryDirectory(prefix='unit-content-tests-', dir=scratch)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.receipt = verify_bundle(DEFAULT_OUTPUT)
        cls.catalog = json.loads((DEFAULT_OUTPUT / 'catalog.json').read_text())
        cls.data = prepare(cls.root / 'demo-data')

    def test_real_mapping_and_all_existing_demo_ids(self):
        units = self.catalog['units']
        self.assertEqual(units['100000102']['name'], 'Rain')
        self.assertEqual(units['100000202']['name'], 'Lasswell')
        self.assertEqual(units['100004203']['name'], 'Ludmille')
        self.assertEqual((len(units), self.receipt['named_ids']), (3311, 3089))
        ids = {json.loads(line)['3HriTp6B'] for line in (self.data / 'mst_decoded/F_UNIT_MST.ndjson').read_text().splitlines()}
        self.assertEqual(len(ids), 423)
        self.assertTrue(all(units[uid]['name'] for uid in ids))

    def test_rarity_follows_master_and_actual_awakening_chain(self):
        for uid, rarity in [('100004203', 3), ('100004204', 4), ('100004205', 5)]:
            unit = self.catalog['units'][uid]
            self.assertEqual(unit['rarity_code'], rarity)
            self.assertEqual(unit['base_rarity_code'], 3)
            self.assertEqual(unit['max_awakening_rarity_code'], 5)
        self.assertNotIn('unverified', self.catalog['units'])
        self.assertEqual(sum(not v['name'] for v in self.catalog['units'].values()), 222)

    def test_exact_id_artwork_and_unmodified_png_checksums(self):
        lock = load_lock()
        self.assertEqual(len(lock['artwork']), 3)
        for art in lock['artwork']:
            relative = self.catalog['units'][art['unit_id']]['artwork']
            self.assertEqual(relative, 'sprites/' + art['unit_id'] + '.png')
            self.assertEqual(sha((DEFAULT_OUTPUT / relative).read_bytes()), art['sha256'])
        # A different form with the same character name never inherits an image.
        self.assertEqual(self.catalog['units']['100004204']['name'], 'Ludmille')
        self.assertIsNone(self.catalog['units']['100004204']['artwork'])

    def test_repeat_import_is_deterministic_and_read_only(self):
        destination = self.root / 'repeat'
        first = import_content(DEFAULT_SOURCE, destination)
        before = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()}
        second = import_content(DEFAULT_SOURCE, destination)
        self.assertEqual(first, second)
        self.assertEqual(before, {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()})

    def test_corrupt_source_and_artwork_are_rejected(self):
        source = self.root / 'bad-source'
        shutil.copytree(DEFAULT_SOURCE, source)
        entry = load_lock()['members'][0]
        (source / entry['name']).write_bytes(b'wrong input')
        destination = self.root / 'must-not-exist'
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            import_content(source, destination)
        self.assertFalse(destination.exists())
        output = self.root / 'bad-output'
        shutil.copytree(DEFAULT_OUTPUT, output)
        (output / 'sprites/100004203.png').write_bytes(b'wrong PNG')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            verify_bundle(output)

    def test_old_save_and_backend_transactions_unchanged(self):
        save = self.root / 'legacy.json'
        service = SummonService(self.data, save, demo=True, initial_lapis=10000)
        service.summon('9100203')
        before, saved = service.state(), save.read_bytes()
        catalogue = copy.deepcopy(service.catalogue)
        # Import and presentation lookup never receive a service or save path.
        import_content(DEFAULT_SOURCE, self.root / 'independent-import')
        restored = SummonService(self.data, save, demo=True)
        self.assertEqual(restored.state(), before)
        self.assertEqual(save.read_bytes(), saved)
        self.assertEqual(restored.catalogue, catalogue)
        result = restored.summon('9100203', 'secondary')
        self.assertEqual(result['state']['currencies']['lapis_free'], 4500)
        self.assertEqual(len(result['result']['awards']), 11)
        self.assertTrue(any(int(a['granted_rarity']) >= 4 for a in result['result']['awards']))

    def test_explicit_demo_build_needs_no_imported_assets(self):
        sys.path.insert(0, str(IOS / 'native/scripts'))
        from package_python import package_content
        output = self.root / 'demo-content'
        package_content(output, mode='demo')
        content = json.loads((output / 'catalog.json').read_text())
        self.assertEqual(content, {'schema': 1, 'mode': 'demo', 'units': {}})
        self.assertFalse((output / 'sprites').exists())

    def test_swift_render_data_and_local_png_decoding(self):
        binary = self.root / 'unit-content-smoke'
        subprocess.run(['xcrun', 'swiftc', '-module-cache-path', str(IOS / '.local/swift-cache'),
                        str(IOS / 'native/FFBERevival/API.swift'), str(IOS / 'native/FFBERevival/UnitContent.swift'),
                        str(IOS / 'native/tests/UnitContentSmoke.swift'), '-o', str(binary)], check=True)
        subprocess.run([str(binary), str(DEFAULT_OUTPUT)], check=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)

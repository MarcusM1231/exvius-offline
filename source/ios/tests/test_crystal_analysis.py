"""Pinned format evidence, bounds, tree integrity and version separation."""
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
sys.dont_write_bytecode = True
IOS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IOS/'content_tools'))
import analyze_crystal_bmb as analysis
from import_crystal_preview import read_source
from crystal_formats import ibmb_records, ibmb_resource_tables, ibmb_word_differences


class CrystalAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lock = json.loads(analysis.LOCK.read_text())
        cls.normal, cls.gold, cls.tutorial = [read_source(lock['sources'][k]) for k in ['crystal-n1', 'crystal-r1', 'tutorial-n1']]

    def test_exact_primary_record_partition_and_tree_candidates(self):
        result = ibmb_records(self.normal)
        self.assertEqual(result['region'], [0x60, 0x6380])
        rows = result['records']
        self.assertEqual(len(rows), 16)
        self.assertEqual([r['offset'] for r in rows if r['raw_type']==3], [0x5400, 0x5bc0])
        self.assertEqual(rows[-1]['preorder_parent_candidate'], 0x2ae0)
        self.assertFalse(result['timeline_decoded'])

    def test_newer_layout_dependencies_are_not_primary_bindings(self):
        rows = ibmb_records(self.tutorial)['records']
        self.assertEqual(len(rows), 65)
        tables = ibmb_resource_tables(self.tutorial)
        self.assertEqual(len(tables['texture_dependencies']), 16)
        self.assertEqual(len(tables['model_dependencies']), 8)
        self.assertEqual(tables['model_dependencies'][0]['name'], 'model_mothercrystal_001')
        self.assertEqual(tables['texture_dependencies'][0]['name'], 'deff_mothercrystal_004')
        with self.assertRaisesRegex(ValueError, 'layout'):
            ibmb_resource_tables(self.normal)

    def test_primary_color_differences_are_not_model_tint(self):
        rows = ibmb_word_differences(self.normal, self.gold)
        self.assertEqual(len(rows), 21)
        self.assertEqual({r['raw_type'] for r in rows if r['record_offset'] is not None}, {6})
        self.assertEqual([r['offset'] for r in rows[:3]], [0x31d0, 0x31d4, 0x31d8])
        self.assertEqual(ibmb_word_differences(self.normal, self.normal), [])
        with self.assertRaisesRegex(ValueError, 'comparison'):
            ibmb_word_differences(self.normal, self.tutorial)

    def test_invalid_sizes_versions_and_hierarchy(self):
        for offset, value in [(4, 999), (0x64, 0), (0x64, 0xfffffffc), (0x68, 4097), (0x68, 0), (0x68, 2)]:
            body = bytearray(self.normal)
            struct.pack_into('<I', body, offset, value)
            with self.assertRaises(ValueError):
                ibmb_records(body)
        with self.assertRaises(ValueError):
            ibmb_records(self.normal[:0x100])

    def test_resource_bounds_and_exact_string_boundaries(self):
        for field, value in [(0x10, 0xffffffff), (0x20, 0xffffffff)]:
            body = bytearray(self.tutorial)
            struct.pack_into('<I', body, field, value)
            with self.assertRaises(ValueError):
                ibmb_resource_tables(body)
        body = bytearray(self.tutorial)
        base = struct.unpack_from('<I', body, 0x5c)[0]
        table = base + struct.unpack_from('<I', body, 0x20)[0]
        struct.pack_into('<Q', body, table, 1)
        with self.assertRaisesRegex(ValueError, 'name boundary'):
            ibmb_resource_tables(body)

    def test_offline_reproducibility_and_scope(self):
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')):
            report = analysis.analyze()
            self.assertEqual(report, analysis.analyze())
        self.assertFalse(report['original_animation_recovered'])
        self.assertFalse(report['findings']['crystal-n1']['compatible_with_observed_memorial_reader'])
        self.assertTrue(report['findings']['tutorial-n1']['compatible_with_observed_memorial_reader'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

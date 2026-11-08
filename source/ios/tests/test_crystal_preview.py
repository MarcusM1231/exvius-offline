"""Bounded observed-format decoding and isolated diagnostic packaging."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import import_crystal_preview as importer
import recover_crystal_dependencies as recovery
from crystal_formats import ibmb_info,m3r_mesh

class CrystalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock=json.loads(importer.LOCK.read_text())
        cls.mesh=importer.read_source(cls.lock['sources']['mother-001'])
        cls.effect=importer.read_source(cls.lock['sources']['crystal-n1'])
    def test_original_geometry_bounds_and_texture_identity(self):
        m=m3r_mesh(self.mesh)
        self.assertEqual((m['vertices'],m['triangles']),(960,320))
        self.assertEqual(m['texture_names'],['deff_mothercrystal_001'])
        self.assertEqual(len(m['indices']),960);self.assertEqual(max(m['indices']),959)
        self.assertLess(m['bounds'][1][0],-11);self.assertGreater(m['bounds'][1][1],13)
    def test_ibmb_name_region_and_unknown_semantics(self):
        r=ibmb_info(self.effect)
        self.assertEqual((r['raw_tag_04'],r['raw_tag_08']),(81,65))
        self.assertIn('model_mothercrystal_001',[x['name'] for x in r['names']])
        self.assertFalse(r['timeline_decoded']);self.assertFalse(r['material_binding_decoded'])
        chest=ibmb_info(importer.read_source(self.lock['sources']['ex-blue']))
        self.assertIn('EX16_chesttop',[x['name'] for x in chest['names']])
        self.assertNotIn('model_mothercrystal_001',[x['name'] for x in chest['names']])
    def test_invalid_headers_counts_and_offsets(self):
        for offset,value in [(4,999),(8,2),(24,0xffffffff),(28,0xffffffff)]:
            b=bytearray(self.mesh);struct.pack_into('<I',b,offset,value)
            with self.assertRaises(ValueError):m3r_mesh(b)
        for body in [b'IBMB',self.effect[:100],b'xxxx'+self.effect[4:]]:
            with self.assertRaises(ValueError):ibmb_info(body)
    def test_bad_indices_and_nonfinite_vertices(self):
        m=m3r_mesh(self.mesh);b=bytearray(self.mesh)
        struct.pack_into('<H',b,m['sections']['indices'],65535)
        with self.assertRaisesRegex(ValueError,'index'):m3r_mesh(b)
        b=bytearray(self.mesh);struct.pack_into('<f',b,m['sections']['vertices'],float('nan'))
        with self.assertRaisesRegex(ValueError,'Non-finite'):m3r_mesh(b)
    def test_checksum_corruption_missing_and_reproducibility(self):
        row=copy.deepcopy(self.lock['sources']['mother-001']);row['stored_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'checksum'):importer.read_source(row)
        row['cache_path']='does-not-exist'
        with self.assertRaises(FileNotFoundError):importer.read_source(row)
        with tempfile.TemporaryDirectory() as temp,patch('socket.socket',side_effect=AssertionError('Network forbidden')):
            output=Path(temp)/'bundle';a=importer.run(output);self.assertEqual(a,importer.run(output))
            (output/'mesh.json').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'checksum'):importer.verify(output)
    def test_dependency_cache_reuses_pins_without_network(self):
        class NoNetwork:
            def read(self,*args):raise AssertionError('Unexpected download')
        self.assertEqual(recovery.run(NoNetwork())['members'],11)
    def test_fresh_dependency_ranges_match_and_never_overwrite(self):
        lock=json.loads(recovery.LOCK.read_text());calls=[]
        blobs={}
        for row in lock['members']:
            source=lock['sources'][row['source']]
            blobs[(source['zip_payload_start']+row['offset_in_cpk'],row['size'])]=(recovery.CACHE/row['cache_path']).read_bytes()
        class MemoryRanges:
            def read(self,source,offset,length):
                calls.append((offset,length));return blobs[(offset,length)]
        with tempfile.TemporaryDirectory() as temp,patch.object(recovery,'CACHE',Path(temp)):
            recovery.run(MemoryRanges());self.assertEqual(len(calls),11)
            row=lock['members'][0];path=Path(temp)/row['cache_path'];path.write_bytes(b'corrupt cache')
            with self.assertRaisesRegex(ValueError,'checksum'):recovery.run(MemoryRanges())
            self.assertEqual(path.read_bytes(),b'corrupt cache')

    def test_preview_has_no_backend_or_network_entry_points(self):
        swift=(IOS/'native/FFBERevival/CrystalPreview.swift').read_text()
        for forbidden in ['PythonWorker','EmbeddedSummonBackend','SummonBackend','URLSession','roll_gacha','campaign.json']:
            self.assertNotIn(forbidden,swift)
        self.assertTrue(all(s['provenance']=='global-targeted-preservation' for s in self.lock['sources'].values()))

if __name__=='__main__':unittest.main(verbosity=2)

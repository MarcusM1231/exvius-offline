"""Original identity, opaque effect textures, bounded pins and offline reconstruction."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
IOS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(IOS/'content_tools'))
import import_crystal_reconstruction as importer
import recover_crystal_reconstruction as recovery
from import_crystal_preview import read_source, sha
from crystal_formats import m3r_mesh
from png_validation import png_info

class ReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock=json.loads(importer.LOCK.read_text())
        cls.bodies={k:read_source(r) for k,r in cls.lock['sources'].items()}

    def test_exact_source_geometry_and_unmodified_coordinates(self):
        expected={'model001':(960,320),'model002':(960,320),'model003':(450,150),'model004':(958,320),'model005':(960,320)}
        for key,counts in expected.items():
            b=self.bodies[key];m=m3r_mesh(b)
            self.assertEqual((m['vertices'],m['triangles']),counts)
            v=m['sections']['vertices']
            self.assertEqual(m['positions'][:3],list(struct.unpack_from('<3f',b,v)))
            self.assertEqual(m['uvs'][:2],list(struct.unpack_from('<2f',b,v+28)))
            self.assertEqual(m['indices'][:3],[0,1,2])
        self.assertEqual(m3r_mesh(self.bodies['model003'])['texture_names'],['space_003'])

    def test_only_observed_ba_vertex_padding_is_accepted(self):
        for key in ['model003','model004']:
            body=bytearray(self.bodies[key]);m=m3r_mesh(body)
            padding=m['sections']['vertices']+m['vertices']*36
            self.assertEqual(body[padding:m['sections']['uninterpreted_tail']],b'\xba'*8)
            body[padding]=0
            with self.assertRaisesRegex(ValueError,'buffer lengths'):m3r_mesh(body)

    def test_effect_png_integrity_without_unit_art_transparency_requirement(self):
        for key in ['texture001','texture002','texture004','prismatic','glow','halo','burst']:
            info=png_info(self.bodies[key],require_transparency=False)
            self.assertGreater(info['width'],0)
        b=bytearray(self.bodies['prismatic']);b[-5]^=1
        with self.assertRaises(ValueError):png_info(b,require_transparency=False)

    def test_cache_only_import_and_immutable_output(self):
        with tempfile.TemporaryDirectory() as temp,patch('socket.socket',side_effect=AssertionError('Network forbidden')):
            target=Path(temp)/'bundle';r=importer.run(target)
            self.assertEqual(r,importer.run(target))
            for key in ['texture001','texture002','texture004','prismatic','glow','halo','burst']:
                self.assertEqual((target/(key+'.png')).read_bytes(),self.bodies[key])
            (target/'model001.json').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'checksum'):importer.verify(target)
            with self.assertRaises(ValueError):importer.run(target)

    def test_changed_manifest_and_missing_source_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'bundle';importer.run(target)
            r=json.loads((target/'receipt.json').read_text());r['files']['../outside']='0'*64
            (target/'receipt.json').write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'receipt'):importer.verify(target)
        row=copy.deepcopy(self.lock['sources']['model001']);row['stored_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'checksum'):read_source(row)
        row['cache_path']='not-present'
        with self.assertRaises(FileNotFoundError):read_source(row)

    def test_pinned_recovery_is_offline_and_preserves_corrupt_cache(self):
        class NoNetwork:
            def read(self,*args):raise AssertionError('Unexpected range')
        self.assertEqual(recovery.run(NoNetwork())['network_bytes'],0)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            # Keep verified indexes in the real discovery cache; isolate only selected bodies.
            for source in self.lock['range_sources'].values():
                name=source['archive']+'-'+Path(source['name']).name+'.json'
                path=root/'discovery'/name;path.parent.mkdir(exist_ok=True)
                path.write_bytes((recovery.CACHE/'discovery'/name).read_bytes())
            first=self.lock['members'][0];path=root/first['cache_path'];path.parent.mkdir(parents=True);path.write_bytes(b'bad')
            with patch.object(recovery,'CACHE',root):
                with self.assertRaisesRegex(ValueError,'checksum'):recovery.run(NoNetwork())
            self.assertEqual(path.read_bytes(),b'bad')

    def test_fresh_six_member_ranges_and_index_identity(self):
        lock=self.lock;calls=[]
        original=recovery.CACHE
        payloads={}
        for row in lock['members']:
            source=lock['range_sources'][row['source']]
            payloads[(source['zip_payload_start']+row['offset_in_cpk'],row['size'])]=(original/row['cache_path']).read_bytes()
        class MemoryRanges:
            def read(self,source,offset,size):
                calls.append((offset,size));return payloads[(offset,size)]
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for source in lock['range_sources'].values():
                name=source['archive']+'-'+Path(source['name']).name+'.json'
                path=root/'discovery'/name;path.parent.mkdir(exist_ok=True)
                path.write_bytes((original/'discovery'/name).read_bytes())
            with patch.object(recovery,'CACHE',root):
                recovery.run(MemoryRanges())
                self.assertEqual(len(calls),6)
                self.assertEqual(recovery.run(MemoryRanges())['members'],6)
                self.assertEqual(len(calls),6)
                changed=copy.deepcopy(lock);changed['members'][0]['offset_in_cpk']+=1
                path=root/'bad.lock.json';path.write_text(json.dumps(changed))
                with patch.object(recovery,'LOCK',path):
                    with self.assertRaisesRegex(ValueError,'identity'):recovery.run(MemoryRanges())

    def test_swift_timeline(self):
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as temp:
            exe=Path(temp)/'clock'
            subprocess.run(['xcrun','swiftc','-module-cache-path',str(IOS/'.local/swift-cache'),str(IOS/'native/FFBERevival/CrystalPlayback.swift'),str(IOS/'native/tests/CrystalPlaybackSmoke.swift'),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True)

    def test_preview_has_no_transaction_or_network_entry_points(self):
        for name in ['CrystalReconstruction.swift','CrystalPlayback.swift','CrystalReconstructionDiagnostics.swift']:
            body=(IOS/'native/FFBERevival'/name).read_text()
            for forbidden in ['PythonWorker','EmbeddedSummonBackend','SummonBackend','URLSession','roll_gacha','campaign.json']:
                self.assertNotIn(forbidden,body)
        self.assertEqual({r['provenance'] for r in self.lock['sources'].values()},{'global-targeted-preservation'})

if __name__=='__main__':unittest.main(verbosity=2)

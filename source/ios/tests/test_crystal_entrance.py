"""Bounded original prompt import and deterministic shared-clock entrance contracts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import import_crystal_entrance as importer
class EntranceTests(unittest.TestCase):
    def test_shared_clock_deterministic_fall_tap_and_lifecycle(self):
        with tempfile.TemporaryDirectory() as t:
            binary=Path(t)/'entrance'
            names=['API.swift','CrystalPlayback.swift','TapSummonState.swift','CrystalEntrance.swift']
            subprocess.run(['xcrun','swiftc','-module-cache-path',str(IOS/'.local/swift-cache'),*[str(IOS/'native/FFBERevival'/n) for n in names],str(IOS/'native/tests/CrystalEntranceSmoke.swift'),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True)
    def test_original_pixels_reproducible_offline(self):
        lock=json.loads(importer.LOCK.read_text());before=[(importer.CACHE/r['cache_path']).read_bytes() for r in lock['members']]
        with tempfile.TemporaryDirectory() as t,patch('socket.socket',side_effect=AssertionError('no network')):
            p=Path(t);a=importer.run(p);self.assertEqual(a,importer.run(p))
            for row,body in zip(lock['members'],before):self.assertEqual((p/(row['id']+'.png')).read_bytes(),body)
        self.assertEqual(before,[(importer.CACHE/r['cache_path']).read_bytes() for r in lock['members']])
    def test_corrupt_sources_and_outputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);importer.run(p/'out');(p/'out/touchscreen.png').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'checksum'):importer.verify(p/'out')
            with self.assertRaisesRegex(ValueError,'overwrite'):importer.run(p/'out')
            row=json.loads(importer.LOCK.read_text())['members'][0];bad=p/'sources'/row['cache_path'];bad.parent.mkdir(parents=True);bad.write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'checksum'):importer.run(p/'other',cache=p/'sources')
    def test_pinned_common_prompt_recovery_uses_complete_cache(self):
        import recover_crystal_entrance as recovery
        class NoNetwork:
            transferred=0
            def read(self,*args):raise AssertionError('Complete cache must remain offline')
        self.assertEqual(recovery.run(NoNetwork()),{'members':1,'network_bytes':0})
    def test_missing_optional_bundle_and_runtime_pin(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(OSError):importer.verify(Path(t))
        source=(IOS/'native/FFBERevival/CrystalEntranceResources.swift').read_text()
        self.assertIn(hashlib.sha256(importer.LOCK.read_bytes()).hexdigest(),source)
        self.assertIn('Text("TOUCH SCREEN")',source)

if __name__=='__main__':unittest.main()

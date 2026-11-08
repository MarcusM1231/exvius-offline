"""Static reveal research: bounded cells, hashes, missing data and no campaign calls."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import import_reveal_research as research
from import_summon_ui import decode
from PIL import Image

class RevealResearch(unittest.TestCase):
    def test_reproducible_offline_import_and_exact_cells(self):
        lock=json.loads(research.LOCK.read_text())
        before=[(research.CACHE/r['cache_path']).read_bytes() for r in lock['sources']]
        with tempfile.TemporaryDirectory() as tmp, patch('socket.socket',side_effect=AssertionError('No network')):
            a=research.run(Path(tmp));b=research.run(Path(tmp));self.assertEqual(a,b)
            self.assertEqual(set(a['files']),{n+'.png' for n in lock['cells']}|{'catalog.json'})
            with Image.open(Path(tmp)/'getglow.png') as im:self.assertEqual(im.size,(136,44))
        self.assertEqual(before,[(research.CACHE/r['cache_path']).read_bytes() for r in lock['sources']])
    def test_corrupt_source_rejected_and_missing_output_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);row=json.loads(research.LOCK.read_text())['sources'][0];f=p/row['cache_path'];f.parent.mkdir(parents=True);f.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'checksum'):research.run(p/'out',cache=p)
            with self.assertRaises(OSError):research.verify(p/'missing')
    def test_modified_derivative_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);research.run(p);(p/'getglow.png').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'checksum'):research.verify(p)
            with self.assertRaisesRegex(ValueError,'overwrite'):research.run(p)
            self.assertEqual((p/'getglow.png').read_bytes(),b'corrupt')
    def test_invalid_pointer_duplicate_and_crop_bounds(self):
        lock=json.loads(research.LOCK.read_text());body=decode((research.CACHE/lock['sources'][0]['cache_path']).read_bytes());start=struct.unpack_from('<I',body,16)[0]
        atlas={'gacha_result_animation.png':Image.new('RGBA',(1024,1024))}
        for offset,value,fmt in [(start, len(body)+1,'I'),(start+10,32767,'h'),(start+20,struct.unpack_from('<I',body,start)[0],'I')]:
            b=bytearray(body);struct.pack_into('<'+fmt,b,offset,value)
            with self.assertRaises(ValueError):research.cells(bytes(b),atlas)
        with self.assertRaisesRegex(ValueError,'Missing atlas'):research.cells(body,{})
    def test_research_recovery_is_cache_only_when_complete(self):
        import recover_reveal_unit as unit
        import recover_reveal_stage as stage
        class NoNetwork:
            transferred=0
            def read(self,*args): raise AssertionError('Unexpected network')
        self.assertEqual(unit.run(NoNetwork())['members'],4)
        self.assertEqual(stage.run(NoNetwork())['members'],5)
    def test_unit_recovery_rejects_modified_cached_bytes(self):
        import recover_reveal_unit as unit
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'maria').mkdir();row=json.loads(unit.LOCK.read_text())['members'][0]
            (p/'maria'/row['name']).write_bytes(b'corrupt')
            with patch.object(unit,'CACHE',p), self.assertRaisesRegex(ValueError,'checksum'):
                unit.run()
    def test_preview_is_static_and_has_no_transaction_reference(self):
        text=(IOS/'native/FFBERevival/RevealResearchPreview.swift').read_text()
        for banned in ['SummonModel','PythonWorker','EmbeddedSummonBackend','campaign.json','URLSession','Timer','SCNNode']:
            self.assertNotIn(banned,text)
        self.assertIn('202000203',text);self.assertIn('not yet confirmed',text)

if __name__=='__main__':unittest.main()

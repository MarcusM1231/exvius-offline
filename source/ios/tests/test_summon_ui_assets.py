"""Selected UI import, TexturePacker geometry, corruption and offline reproducibility."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
sys.dont_write_bytecode=True
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import import_summon_ui as ui

class Assets(unittest.TestCase):
    def test_locked_import_repeats_without_network_or_source_changes(self):
        before=ui.LOCK.read_bytes()
        with tempfile.TemporaryDirectory() as temp, patch('socket.socket',side_effect=AssertionError('network forbidden')):
            a=ui.run(Path(temp)/'bundle');b=ui.run(Path(temp)/'bundle')
            self.assertEqual(a,b)
            catalog=json.loads((Path(temp)/'bundle/catalog.json').read_text())
            self.assertEqual(catalog['layouts']['detail']['gacha_banner']['y'],250)
            self.assertIn('single',catalog['assets'])
        self.assertEqual(before,ui.LOCK.read_bytes())
    def test_corrupt_input_and_bundle_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/'bad').write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError,'checksum'):
                ui.source({'cache_path':'bad','sha256':'0'*64},p)
            ui.run(p/'bundle');(p/'bundle/images/single.png').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'checksum'):ui.verify(p/'bundle')
    def test_trim_restores_source_canvas(self):
        image=Image.new('RGBA',(8,8));image.paste((255,0,0,255),(1,2,4,4))
        frame={'frame':'{{1,2},{3,2}}','rotated':False,'sourceSize':'{7,6}','sourceColorRect':'{{2,1},{3,2}}'}
        out=ui.frame_image(image,frame);self.assertEqual(out.size,(7,6));self.assertEqual(out.getpixel((2,1)),(255,0,0,255));self.assertEqual(out.getpixel((0,0))[3],0)
    def test_rotated_legacy_and_format3_frames(self):
        # Clockwise packed red/green pair must restore the original horizontal pair.
        atlas=Image.new('RGBA',(5,5));atlas.putpixel((1,1),(255,0,0,255));atlas.putpixel((1,2),(0,255,0,255))
        legacy={'frame':'{{1,1},{2,1}}','rotated':True,'sourceSize':'{4,3}','sourceColorRect':'{{1,1},{2,1}}'}
        modern={'textureRect':'{{1,1},{1,2}}','textureRotated':True,'spriteSourceSize':'{4,3}','spriteSize':'{2,1}','spriteOffset':'{0,0}'}
        for frame in [legacy,modern]:
            out=ui.frame_image(atlas,frame);self.assertEqual(out.getpixel((1,1)),(255,0,0,255));self.assertEqual(out.getpixel((2,1)),(0,255,0,255))
    def test_invalid_frame_geometry_and_truncated_compression(self):
        with self.assertRaises(ValueError):ui.frame_image(Image.new('RGBA',(1,1)),{'frame':'{{0,0},{2,2}}','sourceSize':'{2,2}','sourceColorRect':'{{0,0},{2,2}}'})
        with self.assertRaises(ValueError):ui.decode(b'CRILAYLA'+b'\x00'*8)
    def test_provenance_and_no_memorial_inputs(self):
        lock=json.loads(ui.LOCK.read_text())
        self.assertEqual({r['provenance'] for r in lock['sources'].values()},{'original-global-ipa','global-targeted-preservation'})
        self.assertTrue(all('memorial' not in r['cache_path'] for r in lock['sources'].values()))
        self.assertTrue(all(lock['sources'][source]['provenance']=='original-global-ipa' for source in lock['layouts'].values()))

if __name__=='__main__':unittest.main(verbosity=2)

import json,sys,unittest,tempfile
from unittest.mock import patch
from pathlib import Path
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
from import_content import sha
from expand_unit_animations import plan,LOCK
import import_unit_animations as importer

class ExpansionTests(unittest.TestCase):
    def test_restore_pinned_member_and_refuse_corrupt_response(self):
        import expand_unit_animations as recovery
        lock=json.loads(LOCK.read_text());row=next(r for r in lock['members'] if r['name']=='unit_anime_202000203.png');body=(IOS/row['cache_path']).read_bytes()
        class Reader:
            transferred=0
            requests=[]
            def read(self,*args):return body
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
            target=Path(tmp)/'restored.png';row=dict(row,cache_path=str(target));lock['members']=[row]
            pinned=Path(tmp)/'lock.json';pinned.write_text(json.dumps(lock))
            with patch.object(recovery,'LOCK',pinned),patch.object(recovery,'ROOT',Path(tmp)),patch.object(recovery,'RangeClient',return_value=Reader()):
                self.assertEqual(recovery.restore_locked(),1);self.assertEqual(target.read_bytes(),body)
                target.unlink()
                with patch.object(Reader,'read',return_value=b'bad'):
                    with self.assertRaises(ValueError):recovery.restore_locked()
                self.assertFalse(target.exists())
    def test_resume_and_duplicate_ids_without_network(self):
        import expand_unit_animations as recovery
        class NoNetwork:
            transferred=0
            requests=[]
            def read(self,*args):raise AssertionError('Resume fetched existing content')
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
            lock=Path(tmp)/'lock.json';lock.write_bytes(LOCK.read_bytes());before=lock.read_bytes()
            with patch.object(recovery,'LOCK',lock),patch.object(recovery,'ROOT',Path(tmp)),patch.object(recovery,'RangeClient',return_value=NoNetwork()):
                self.assertEqual(recovery.run(ids=['202000203']),[])
                self.assertEqual(lock.read_bytes(),before)
                with self.assertRaises(ValueError):recovery.run(ids=['202000203','202000203'])
                with self.assertRaises(ValueError):recovery.run(ids=['999999999'])
    def test_animation_sheet_dimension_budget_is_separate_from_static_art(self):
        from PIL import Image
        from png_validation import png_info
        import io
        image=Image.new('RGBA',(1,2050));image.putpixel((0,0),(255,0,0,255));buffer=io.BytesIO();image.save(buffer,format='PNG');body=buffer.getvalue()
        with self.assertRaises(ValueError):png_info(body,raster=image)
        self.assertEqual(png_info(body,raster=image,maximum_dimension=4096)['height'],2050)
    def test_accelerated_png_validation_matches_strict_decoder(self):
        from PIL import Image
        from png_validation import png_info
        import io
        lock=json.loads(importer.LEGACY_LOCK.read_text())
        for row in lock['members']:
            if not row['name'].endswith('.png'):continue
            body=(IOS/'.local/phase6d4/sources'/row['name']).read_bytes()
            with Image.open(io.BytesIO(body)) as image:
                image.load();self.assertEqual(png_info(body),png_info(body,raster=image))
                damaged=bytearray(body);damaged[-5]^=1
                with self.assertRaises(ValueError):png_info(bytes(damaged),raster=image)
    def test_trailing_empty_csv_padding_is_not_an_extra_part(self):
        from unit_animation import parse_cgg
        text='0,1,0,0,0,0,100,0,0,0,1,1,0'
        self.assertEqual(parse_cgg(text,(1,1)),parse_cgg(text+',,,,,,',(1,1)))
        with self.assertRaises(ValueError):parse_cgg('0,1,0,,0,0,100,0,0,0,1,1,0,,,,',(1,1))
    def test_cardinal_rotation_and_overlay_origin(self):
        from PIL import Image
        from unit_animation import parse_cgg,compose
        texture=Image.new('RGBA',(2,1));texture.putdata([(255,0,0,255),(0,0,255,255)])
        parts=parse_cgg('0,1,0,0,0,0,100,90,0,0,2,1,0',(2,1))[0]
        frame=compose(texture,parts,canvas=(1,2),origin=(0,0))
        self.assertEqual(frame.getpixel((0,0)),(0,0,255,255));self.assertEqual(frame.getpixel((0,1)),(255,0,0,255))
    def test_target_inventory_and_missing_forms(self):
        _,_,rows=plan();targets=json.loads((IOS/'content_tools/content.lock.json').read_text())['targets']['demo_ids']
        self.assertEqual({k for k,v in rows.items() if v['is_target']},set(targets));self.assertEqual(len(targets),423)
        self.assertEqual({k for k,v in rows.items() if not v['source']},{'100000102','100000202','100004203'})
    def test_original_four_source_identity_preserved(self):
        old=json.loads(importer.LEGACY_LOCK.read_text());new=json.loads(LOCK.read_text());entries={r['name']:r for r in new['members']}
        for row in old['members']:
            for key in ['sha256_stored','sha256_decoded','offset_in_cpk','size','unpacked']:
                self.assertEqual(entries[row['name']][key],row[key])
    def test_original_four_rendered_pixels_unchanged(self):
        legacy=IOS/'.local/unit-animations/versions'/sha(importer.LEGACY_LOCK.read_bytes())[:16]/'UnitAnimations'
        old=json.loads((legacy/'catalog.json').read_text())
        current=json.loads((importer.output()/'catalog.json').read_text())
        for uid,clips in old.items():
            for kind,meta in clips.items():
                self.assertEqual(current[uid][kind],meta)
                for name in meta['frames']:self.assertEqual((legacy/name).read_bytes(),(importer.output()/name).read_bytes())
    def test_all_pinned_sources_and_indexes(self):
        lock=json.loads(LOCK.read_text())
        for source in lock['sources'].values():self.assertEqual(sha((IOS/source['index_path']).read_bytes()),source['index_sha256'])
        names=set()
        for row in lock['members']:
            self.assertNotIn(row['name'],names);names.add(row['name'])
            self.assertEqual(len(importer.checked(row['name'],lock)),row['unpacked'])
    def test_bundle_coverage_and_budgets(self):
        importer.verify();root=importer.output();catalog=json.loads((root/'catalog.json').read_text());coverage=json.loads((root/'coverage.json').read_text())
        self.assertEqual(len(coverage),425)
        self.assertGreaterEqual(sum('idle' in v for v in catalog.values()),25)
        for uid,clips in catalog.items():
            for kind,m in clips.items():
                self.assertEqual(m['masterID'],uid);self.assertEqual(m['kind'],kind)
                self.assertLessEqual(len(m['frames']),64);self.assertLessEqual(m['width']*m['height']*len(m['frames'])*4,8388608)
                self.assertTrue(all(1<=t<=600 for t in m['ticks']));self.assertEqual(len(m['ticks']),len(m['frames']))
                self.assertTrue(all(abs(v)<=512 for v in m['anchor']))
        for uid,row in coverage.items():
            if 'idle' not in row['supported']:self.assertTrue(row['reason'])
if __name__=='__main__':unittest.main()

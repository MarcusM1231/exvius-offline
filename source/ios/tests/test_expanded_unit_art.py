import json,sys,tempfile,shutil,copy,unittest,io
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import expanded_unit_art as art
from PIL import Image
class ExpandedArtTests(unittest.TestCase):
 def test_every_reward_form_accounted_and_exact_rarity(self):
  coverage=json.loads((art.ROOT/'coverage.json').read_text());self.assertEqual(len(coverage['records']),844);self.assertEqual(sum(r['static_before'] for r in coverage['records']),426)
  lock=json.loads(art.LOCK.read_text());ids={r['unit_id'] for r in lock['artwork']};self.assertEqual(ids,{r['unit_id'] for r in coverage['records'] if r['status']=='recovered'})
  self.assertGreater(len(ids),400)
  for r in lock['artwork']:self.assertEqual(Path(r['entry']['name']).name,'unit_ills_'+r['unit_id']+'.png');self.assertTrue(r['transparent']);self.assertEqual(r['provenance'],'original static PNG member')
 def test_source_checksums_decode_transparency_bounds_and_reproducibility(self):
  receipt=(art.output()/'receipt.json').read_bytes();art.import_bundle();self.assertEqual(receipt,(art.output()/'receipt.json').read_bytes());art.verify()
  rows=json.loads(art.LOCK.read_text())['artwork'];self.assertTrue(any(r['entry']['size']!=r['entry']['unpacked'] for r in rows))
  for row in rows:
   body=art.decode((IOS/row['cache_path']).read_bytes());info=art.png(body);self.assertEqual(info['dimensions'],row['dimensions']);self.assertGreater(info['visible_bounds'][2],info['visible_bounds'][0])
 def test_duplicate_ids_corrupt_bundle_and_source_member_rejected(self):
  lock=json.loads(art.LOCK.read_text())
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'lock.json';p.write_text(json.dumps(dict(lock,artwork=lock['artwork']+[lock['artwork'][0]])))
   with patch.object(art,'LOCK',p):
    with self.assertRaisesRegex(ValueError,'Duplicate'):art.import_bundle()
   target=Path(tmp)/'bundle';shutil.copytree(art.output(),target);next((target/'images').glob('*.png')).write_bytes(b'bad')
   with self.assertRaisesRegex(ValueError,'checksum'):art.verify(target)
   lock['artwork'][0]['entry']['offset_in_cpk']+=1;p.write_text(json.dumps(lock))
   with patch.object(art,'LOCK',p):
    with self.assertRaisesRegex(ValueError,'member mismatch'):art.import_bundle()
 def test_cache_only_resume_keeps_animation_discovery_unchanged(self):
  class NoNetwork:
   transferred=0
   def read(self,*args):raise AssertionError('Unexpected network')
  original=IOS/'.local/unit-content/discovery';before={p.name:art.sha(p.read_bytes()) for p in original.glob('*.json')};pin=art.LOCK.read_bytes()
  with patch.object(art,'RangeClient',return_value=NoNetwork()):art.recover()
  self.assertEqual(pin,art.LOCK.read_bytes());self.assertEqual(before,{p.name:art.sha(p.read_bytes()) for p in original.glob('*.json')})
 def test_inventory_reuses_existing_indexes_without_network(self):
  class NoNetwork:
   transferred=0
   def read(self,*args):raise AssertionError('Cached index downloaded again')
  primary=IOS/'.local/unit-content/discovery';sources=json.loads(art.LOCK.read_text())['source_pins']
  with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
   target=Path(tmp);(target/'discovery').mkdir()
   for key,source in sources.items():
    if not (primary/(key+'.json')).exists():shutil.copy2(IOS/source['index_path'],target/'discovery'/(key+'.json'))
   with patch.object(art,'ROOT',target),patch.object(art,'RangeClient',return_value=NoNetwork()):report=art.inventory()
   self.assertEqual(len(report['source_pins']),36);self.assertEqual(len(list((target/'discovery').glob('*.json'))),36)
 def test_opaque_empty_and_corrupt_png_rejected(self):
  for mode,color in [('RGB',(255,0,0)),('RGBA',(0,0,0,0))]:
   stream=io.BytesIO();Image.new(mode,(2,2),color).save(stream,format='PNG')
   with self.assertRaises(ValueError):art.png(stream.getvalue())
  with self.assertRaises(ValueError):art.png(b'not PNG')
 def test_content_deduplicated_and_animation_priority_unchanged(self):
  lock=json.loads(art.LOCK.read_text());self.assertEqual(len(list((art.output()/'images').glob('*.png'))),len({r['sha256'] for r in lock['artwork']}))
  text=(IOS/'native/FFBERevival/UnitContent.swift').read_text();self.assertIn(art.sha(art.LOCK.read_bytes()),text);self.assertIn('images/\\(hash).png',text)
  view=(IOS/'native/FFBERevival/UnitArtworkView.swift').read_text();self.assertIn('interpolation(.none)',view);self.assertIn('c.countLimit=64',view)
  reveal=(IOS/'native/FFBERevival/SummonCharacterReveal.swift').read_text();self.assertIn('unitMotion.load(masterID:award.unit_id)',reveal)
if __name__=='__main__':unittest.main()

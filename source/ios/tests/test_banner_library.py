import json,sys,copy,tempfile,shutil,unittest
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import import_banner_library as lib
import recover_banner_library as recovery
from import_content import sha
class LibraryTests(unittest.TestCase):
 def test_all_indexed_candidates_classified_and_no_missing_rows(self):
  report=json.loads((recovery.ROOT/'classification.json').read_text());inv=json.loads((recovery.ROOT/'inventory.json').read_text());keys={r['key'] for r in inv['candidates']}
  self.assertEqual(keys,{r['key'] for r in report['records']});self.assertEqual(len(keys),542)
  self.assertEqual(sum(r['filename_referenced'] for r in report['records']),533)
  self.assertEqual(sum(r['status']=='successfully_recovered' for r in report['records']),532)
  self.assertEqual(sum(r['status']=='found_but_unsupported_size' for r in report['records']),1)
  self.assertEqual(sum(r['status']=='unmatched_or_unverified_language' for r in report['records']),9)
 def test_exact_role_mapping_extra_panels_and_deduplication(self):
  lib.verify();catalog=json.loads((lib.output()/'catalog.json').read_text());lock=json.loads(lib.LOCK.read_text());self.assertIn('banner',catalog['49']);self.assertIn('detail_extra_0',catalog['9200001'])
  for row in lock['artwork']:
   for m in row['mapping']:
    if m['role']=='detail_extra':continue
    a=catalog[m['banner_id']][m['role']];self.assertEqual(a['file'],'images/'+row['sha256']+'.png');self.assertEqual([a['width'],a['height']],[row['width'],row['height']])
  self.assertEqual(len(list((lib.output()/'images').glob('*.png'))),len({r['sha256'] for r in lock['artwork']}))
 def test_duplicate_source_and_corrupt_outputs_rejected(self):
  lock=json.loads(lib.LOCK.read_text())
  with tempfile.TemporaryDirectory(dir=IOS/'.local') as temp:
   p=Path(temp);copylock=p/'lock.json';copylock.write_text(json.dumps(dict(lock,artwork=lock['artwork']+[lock['artwork'][0]])))
   with patch.object(lib,'LOCK',copylock):
    with self.assertRaises(ValueError):lib.run()
   target=p/'art';shutil.copytree(lib.output(),target);next((target/'images').glob('*.png')).write_bytes(b'corrupt')
   with self.assertRaises(ValueError):lib.verify(target)
 def test_reproducibility_and_cache_resume_without_network(self):
  before=(lib.output()/'receipt.json').read_bytes();lib.run();self.assertEqual(before,(lib.output()/'receipt.json').read_bytes())
  class NoNetwork:
   transferred=0
   def read(self,*a):raise AssertionError('Network used for verified cache')
  old=recovery.LOCK.read_bytes()
  with patch.object(recovery,'RangeClient',return_value=NoNetwork()):recovery.recover()
  self.assertEqual(old,recovery.LOCK.read_bytes())
 def test_native_pin_and_bounded_lazy_decode(self):
  text=(IOS/'native/FFBERevival/OriginalBannerMenu.swift').read_text();self.assertIn(sha(lib.LOCK.read_bytes()),text)
  for expected in ['cache.countLimit=16','cache.totalCostLimit=12*1024*1024','CGImageSourceThumbnailMaxPixelSize','LazyVStack','onDisappear {image=nil}','--banner-art-missing']:self.assertIn(expected,text)
  self.assertNotIn('URLSession',text)
 def test_zip_bounds_crc_and_png_checks(self):
  with self.assertRaises(ValueError):recovery.decode_member(b'bad',0,{'offset':0})
  row=json.loads(lib.LOCK.read_text())['artwork'][0];raw=(IOS/row['cache_path']).read_bytes();entry=copy.deepcopy(row['entry']);entry['crc32']^=1
  with self.assertRaises(ValueError):recovery.validate(raw,entry)
if __name__=='__main__':unittest.main()

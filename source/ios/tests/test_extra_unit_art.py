import json,sys,tempfile,shutil,unittest
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import import_extra_unit_art as art
class ExtraArtTests(unittest.TestCase):
 def test_exact_forms_and_reproducible_offline_import(self):
  class NoNetwork:
   transferred=0
   def read(self,*args):raise AssertionError('Unexpected network')
  before=(art.output()/'receipt.json').read_bytes()
  with patch.object(art,'RangeClient',return_value=NoNetwork()):art.run()
  self.assertEqual(before,(art.output()/'receipt.json').read_bytes())
  catalog=json.loads((art.output()/'catalog.json').read_text())
  self.assertEqual(set(catalog),{'206000504','100004104','100004105'})
  for uid,row in catalog.items():self.assertEqual(row['file'],'sprites/'+uid+'.png')
 def test_duplicate_id_and_source_entry_mismatch_rejected(self):
  lock=json.loads(art.LOCK.read_text())
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'lock.json';path.write_text(json.dumps(dict(lock,artwork=lock['artwork']+[lock['artwork'][0]])))
   with patch.object(art,'LOCK',path):
    with self.assertRaisesRegex(ValueError,'Duplicate'):art.run()
   lock['artwork'][0]['entry']['offset_in_cpk']+=1;path.write_text(json.dumps(lock))
   with patch.object(art,'LOCK',path):
    with self.assertRaisesRegex(ValueError,'entry mismatch'):art.run()
 def test_corrupted_png_and_missing_file_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)/'art';shutil.copytree(art.output(),target)
   png=next((target/'sprites').glob('*.png'));png.write_bytes(b'corrupt')
   with self.assertRaisesRegex(ValueError,'checksum'):art.verify(target)
   png.unlink()
   with self.assertRaisesRegex(ValueError,'file set'):art.verify(target)
if __name__=='__main__':unittest.main()

import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import banner_catalogue as catalog
import import_banner_research as importer
from import_content import sha
class BannerResearchTests(unittest.TestCase):
 def test_projection_is_detached_and_does_not_invent_offers(self):
  banner={'id':'123','name':'Fixture','type':'normal','cost':{'kind':'lapis','amount':500},'draws':1,'pool':[{'unit_id':'100000102','rate':1,'rarity':2}]}
  before=copy.deepcopy(banner)
  r=catalog.project([banner],[{'id':'standard','ids':['123']}],{},lambda b:1,lambda b:True,demo_ids=['123'],ios_unit_ids=['100000102'])
  self.assertEqual(banner,before);self.assertTrue(r['records'][0]['single']);self.assertFalse(r['records'][0]['multi'])
  r['records'][0]['offers'][0]['cost']['amount']=0;self.assertEqual(banner,before)
  with self.assertRaises(ValueError):catalog.project([banner,banner],[],{},lambda b:1,lambda b:True)
 def test_actual_catalogue_without_player_or_save(self):
  with tempfile.TemporaryDirectory(dir=IOS/'.local') as temp:
   out=Path(temp)/'catalog.json'
   subprocess.run([sys.executable,str(IOS/'content_tools/banner_catalogue.py'),'--output',str(out)],check=True,capture_output=True)
   r=json.loads(out.read_text());self.assertEqual(len(r['records']),745);self.assertEqual(sum(v['visible_in_archive'] for v in r['records']),469)
   self.assertFalse(r['campaign_accessed']);self.assertEqual(r['transactions'],0)
   self.assertEqual({v['id'] for v in r['records'] if v['ios_integration'].startswith('existing')},{'49','9100203'})
   self.assertEqual({v['id'] for v in r['disabled_definitions']},{'71001','71002'})
   self.assertEqual(len([v for v in r['records'] if any('step.pool' in e for e in v['known_issues'])]),6)
 def test_source_pin_and_optional_bundle(self):
  importer.verify();lock=json.loads(importer.LOCK.read_text());root=importer.output();c=json.loads((root/'catalog.json').read_text())
  self.assertTrue(c['read_only']);self.assertEqual(len(c['records']),745);self.assertEqual(sum(bool(r['images']) for r in c['records']),4)
  self.assertIn(sha(importer.LOCK.read_bytes()),(IOS/'native/FFBERevival/BannerResearchPreview.swift').read_text())
  with tempfile.TemporaryDirectory(dir=IOS/'.local') as temp:
   import shutil
   target=Path(temp)/'bundle';shutil.copytree(root,target);(target/'catalog.json').write_text('corrupt')
   with self.assertRaises(ValueError):importer.verify(target)
 def test_art_cache_resume_has_no_network(self):
  import recover_banner_research as recovery
  class NoNetwork:
   transferred=0
   def read(self,*args):raise AssertionError('Unexpected network')
  before=recovery.LOCK.read_bytes()
  with patch.object(recovery,'RangeClient',return_value=NoNetwork()):recovery.recover()
  self.assertEqual(before,recovery.LOCK.read_bytes())
 def test_reproducibility(self):
  before=(importer.output()/'receipt.json').read_bytes()
  subprocess.run([sys.executable,str(IOS/'content_tools/import_banner_research.py')],check=True,capture_output=True)
  self.assertEqual(before,(importer.output()/'receipt.json').read_bytes())
 def test_preview_has_no_transaction_or_campaign_dependency(self):
  text=(IOS/'native/FFBERevival/BannerResearchPreview.swift').read_text()
  for value in ['SummonModel','PythonWorker','EmbeddedSummonBackend','URLSession','roll_gacha','campaign.json']:self.assertNotIn(value,text)
  for relative in ['native/FFBERevival/SummonCharacterReveal.swift','native/FFBERevival/ObtainedUnitMotion.swift','native/FFBERevival/UnitActionSequence.swift','prototype/summon_service.py','content_tools/unit-attack-expanded.lock.json','content_tools/content.lock.json']:
   committed=subprocess.check_output(['git','show','6da00ff:source/ios/'+relative],cwd=IOS)
   self.assertEqual((IOS/relative).read_bytes(),committed,relative)
if __name__=='__main__':unittest.main()

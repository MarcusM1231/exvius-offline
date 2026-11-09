"""Real-engine expanded catalog tests: isolated accounts, original IDs, no normal saves."""
import copy,json,sys,tempfile,subprocess,unittest,hashlib,shutil
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'prototype'));sys.path.insert(0,str(IOS/'content_tools'))
import build_summon_catalog as content
from banner_menu import MenuSummonService
from summon_service import SummonError
class ExpandedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  content.verify();cls.data=content.output();cls.tmp=tempfile.TemporaryDirectory(dir=IOS/'.local');cls.addClassCleanup(cls.tmp.cleanup);cls.root=Path(cls.tmp.name)
 def setUp(self):self.s=MenuSummonService(self.data,self.root/(self._testMethodName+'.json'),demo=True,initial_lapis=100000)
 def test_all_enabled_definitions_have_real_transaction_and_reload_evidence(self):
  audit=json.loads((content.ROOT/'eligibility.json').read_text());passed=[r for r in audit['records'] if r['eligible']]
  self.assertEqual(len(audit['records']),471);self.assertGreater(len(passed),2)
  self.assertEqual(set(self.s.catalogue),{r['id'] for r in passed})
  self.assertTrue(all(o['transaction_and_reload']=='passed' for r in passed for o in r['offers']))
 def test_browsing_is_read_only_with_full_metadata(self):
  before=copy.deepcopy(self.s.player.data);saved=self.s.save_path.read_bytes();dirty=self.s.player.dirty
  with patch.object(self.s.player,'roll_gacha',side_effect=AssertionError('roll')),patch.object(self.s.player,'save',side_effect=AssertionError('save')):
   m=self.s.menu();b=self.s.banners();self.assertEqual(m,self.s.menu())
  self.assertEqual(len(m['banners']),471);self.assertEqual(len(b),len(self.s.catalogue));self.assertEqual(self.s.player.data,before);self.assertEqual(self.s.save_path.read_bytes(),saved);self.assertEqual(self.s.player.dirty,dirty)
 def test_displayed_rates_are_the_actual_python_base_pool(self):
  m=self.s.menu();row=next(b for b in m['banners'] if b['id']=='9');pool=self.s.engine.expand_pool(self.s.catalogue['9']);total=sum(float(r['rate']) for r in pool)
  for rate in row['rates']:
   expected=sum(float(r['rate']) for r in pool if int(r['rarity'])==rate['rarity'])/total
   self.assertAlmostEqual(rate['weight'],expected)
 def test_original_two_pools_prices_and_awarded_rarities_are_unchanged(self):
  code='''import sys,json,tempfile,os
from pathlib import Path
sys.path.insert(0,sys.argv[1]);from demo_data import prepare
from summon_service import SummonService
with tempfile.TemporaryDirectory() as t:
 s=SummonService(prepare(Path(t)/'data'),Path(t)/'save',demo=True)
 out={u:[(r['unit_id'],int(r['rarity']),float(r['rate'])) for r in s.engine.expand_pool(s.catalogue[u])] for u in ['49','9100203']}
 print(json.dumps(out))'''
  result=subprocess.run([sys.executable,'-c',code,str(IOS/'prototype')],capture_output=True,text=True,check=True);old=json.loads(result.stdout)
  for uid in ['49','9100203']:
   actual=[[r['unit_id'],int(r['rarity']),float(r['rate'])] for r in self.s.engine.expand_pool(self.s.catalogue[uid])]
   self.assertEqual(actual,old[uid]);self.assertEqual(self.s.quote(uid)['cost']['amount'],500);self.assertEqual(self.s.quote(uid,'secondary')['cost']['amount'],5000)
 def test_new_single_multi_and_stale_duplicate_no_second_charge(self):
  b=next(b for uid,b in self.s.catalogue.items() if uid not in ['49','9100203'] and b.get('secondary_offer') and b.get('draws',1)==1 and b['secondary_offer'].get('draws')==11)
  uid=str(b['id'])
  for offer,n in [('primary',1),('secondary',11)]:
   q=self.s.quote(uid,offer);before=self.s.state();r=self.s.summon(uid,offer,quote_token=q['quote_token']);self.assertEqual(len(r['result']['awards']),n)
   self.assertEqual(len(r['state']['units']),len(before['units'])+n)
   saved=self.s.save_path.read_bytes()
   with self.assertRaises(SummonError) as e:self.s.summon(uid,offer,quote_token=q['quote_token'])
   self.assertEqual(e.exception.code,'stale_quote');self.assertEqual(self.s.save_path.read_bytes(),saved)
 def test_missing_token_unsupported_ticket_step_box_selection_fail_before_roll(self):
  before=copy.deepcopy(self.s.player.data)
  with patch.object(self.s.player,'roll_gacha',side_effect=AssertionError('roll')):
   for uid in ['9','9200023']:
    with self.assertRaises(SummonError):self.s.summon(uid)
   for b in self.s._definitions().values():
    if b.get('steps') or b.get('boxes') or b.get('selection'):
     q=self.s.quote(str(b['id']));self.assertFalse(q['supported'])
     with self.assertRaises(SummonError):self.s.summon(str(b['id']),quote_token=q['quote_token'])
  self.assertEqual(self.s.player.data,before)
 def test_insufficient_currency_and_save_failure_keep_disk_and_inventory(self):
  q=self.s.quote('9');before=copy.deepcopy(self.s.player.data);saved=self.s.save_path.read_bytes()
  with patch.object(self.s.player,'save',return_value=False):
   with self.assertRaises(SummonError) as e:self.s.summon('9',quote_token=q['quote_token'])
   self.assertEqual(e.exception.code,'save_failed')
  self.assertEqual(self.s.player.data,before);self.assertEqual(self.s.save_path.read_bytes(),saved)
  self.s.player.data['currencies']['lapis_free']=0;self.s.player.data['currencies']['lapis_paid']=0;q=self.s.quote('9');self.assertFalse(q['eligible'])
  before=copy.deepcopy(self.s.player.data)
  with self.assertRaises(SummonError):self.s.summon('9',quote_token=q['quote_token'])
  self.assertEqual(self.s.player.data,before)
 def test_corrupted_metadata_refuses_before_campaign_creation(self):
  target=self.root/'corrupt';shutil.copytree(self.data,target);(target/'mst_decoded/F_UNIT_MST.ndjson').write_text('bad')
  save=self.root/'must-not-exist.json'
  with self.assertRaises(ValueError):MenuSummonService(target,save,demo=True)
  self.assertFalse(save.exists())
 def test_old_save_and_owned_records_upgrade_without_reset(self):
  legacy=self.root/'legacy.json'
  code='''import sys,tempfile
from pathlib import Path
sys.path.insert(0,sys.argv[1]);from demo_data import prepare
from summon_service import SummonService
with tempfile.TemporaryDirectory() as t:
 s=SummonService(prepare(Path(t)/'data'),Path(sys.argv[2]),demo=True,initial_lapis=10000);s.summon('49')'''
  subprocess.run([sys.executable,'-c',code,str(IOS/'prototype'),str(legacy)],capture_output=True,check=True)
  raw=legacy.read_bytes();old=json.loads(raw);s=MenuSummonService(self.data,legacy,demo=True,initial_lapis=999999)
  self.assertEqual(legacy.read_bytes(),raw);self.assertEqual(s.player.data['roster'],old['roster']);self.assertEqual(s.player.currencies,old['currencies'])
  q=s.quote('9');s.summon('9',quote_token=q['quote_token']);self.assertEqual(s.player.data['roster'][:len(old['roster'])],old['roster'])
 def test_ticket_engine_foundation_consumption_floor_reload_and_insufficient(self):
  rows=self.s.engine._load_ndjson('F_TICKET_MST.ndjson')['__rows__'];ticket=next(r for r in rows if int(r.get('9fW0TePj',0)) in [3,4,5])
  typ=int(ticket['89EvGKHx']);item=int(ticket['tL6G9egd']);tid=str(ticket['zJ1A6HXm']);group=str(ticket['zF6QIY2r'])
  self.s.player._grant_items([{'kind':typ,'id':item,'count':1}])
  b=copy.deepcopy(self.s._definitions()['9']);b.pop('cost',None);b.pop('guarantee',None);b['ticket_group_id']=group;b['draws']=1
  lapis=self.s.player.currencies['lapis_free'];r=self.s.player.roll_gacha(b,ticket_id=tid)
  self.assertIsNotNone(r);self.assertEqual(r['ticket_id'],int(tid) if isinstance(r['ticket_id'],int) else tid);self.assertTrue(all(int(a['granted_rarity'])>=int(ticket['9fW0TePj']) for a in r['awards']));self.assertEqual(self.s.player.currencies['lapis_free'],lapis)
  self.s._save();restored=self.s.engine.PlayerState.load(str(self.s.save_path),slot='ios-summons',mode='live');self.assertEqual(restored.data['inventory'],self.s.player.data['inventory'])
  before=copy.deepcopy(self.s.player.data);self.assertIsNone(self.s.player.roll_gacha(b,ticket_id=tid));self.assertEqual(before,self.s.player.data)
 def test_step_foundation_specific_pools_lap_and_reload(self):
  units={int(r['rarity']):r['unit_id'] for r in self.s.engine.expand_pool(self.s._definitions()['9'])}
  b={'id':'fixture-step','steps':[{'cost':{'kind':'lapis','amount':100},'draws':1,'pool':[{'unit_id':units[3],'rarity':3,'rate':1}]},{'cost':{'kind':'lapis','amount':200},'draws':2,'pool':[{'unit_id':units[5],'rarity':5,'rate':1}]}]}
  before=self.s.player.currencies['lapis_free']
  for i in [0,1]:
   r=self.s.player.roll_gacha(b);self.assertIsNotNone(r);self.assertEqual({a['unit_id'] for a in r['awards']},{units[3 if i==0 else 5]})
  self.assertEqual(self.s.player.data['gacha']['step'][b['id']],0);self.assertEqual(self.s.player.data['gacha']['completed_laps'][b['id']],1);self.assertEqual(before-self.s.player.currencies['lapis_free'],300)
  self.s._save();r=self.s.engine.PlayerState.load(str(self.s.save_path),slot='ios-summons',mode='live');self.assertEqual(r.data['gacha'],self.s.player.data['gacha'])
if __name__=='__main__':unittest.main()

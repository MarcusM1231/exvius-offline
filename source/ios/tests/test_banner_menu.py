"""Live quotes and original-menu resources; every account is temporary and isolated."""
import copy,json,sys,tempfile,unittest,subprocess,hashlib
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(IOS/'prototype'));sys.path.insert(0,str(IOS/'content_tools'))
from demo_data import prepare
from banner_menu import MenuSummonService
from summon_service import SummonError
class MenuTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(dir=IOS/'.local');cls.addClassCleanup(cls.temp.cleanup);cls.root=Path(cls.temp.name);cls.data=prepare(cls.root/'data')
 def setUp(self):self.s=MenuSummonService(self.data,self.root/(self._testMethodName+'.json'),demo=True,initial_lapis=10000)
 def test_navigation_and_quotes_do_not_mutate_save_dirty_inventory_rng(self):
  before=copy.deepcopy(self.s.player.data);saved=self.s.save_path.read_bytes();dirty=self.s.player.dirty
  with patch.object(self.s.player,'roll_gacha',side_effect=AssertionError('roll')),patch.object(self.s.player,'save',side_effect=AssertionError('save')):
   a=self.s.menu();b=self.s.menu();self.assertEqual(a,b)
   for banner in a['banners']:
    for offer in banner['offers']:self.s.quote(banner['id'],offer['offer'])
  self.assertEqual(self.s.player.data,before);self.assertEqual(self.s.player.dirty,dirty);self.assertEqual(self.s.save_path.read_bytes(),saved)
  self.assertEqual({r['id'] for r in a['banners'] if r['playable']},{'49','9100203'})
  self.assertEqual({r['category'] for r in a['banners']},{'rare','standard','limited'})
 def test_live_prices_balances_guarantees_and_one_transaction(self):
  for uid in ['49','9100203']:
   self.assertEqual(self.s.quote(uid)['cost']['amount'],500)
   q=self.s.quote(uid,'secondary');self.assertEqual((q['draws'],q['cost']['amount'],q['balance']),(11,5000,10000));self.assertTrue(q['eligible'])
  r=self.s.summon('49');self.assertEqual(len(r['result']['awards']),1)
  self.assertEqual(self.s.quote('49')['balance'],9500)
  r=self.s.summon('49','secondary');self.assertEqual(len(r['result']['awards']),11);self.assertEqual(self.s.quote('49')['balance'],4500)
  before=copy.deepcopy(self.s.player.data);saved=self.s.save_path.read_bytes()
  self.assertFalse(self.s.quote('49','secondary')['eligible'])
  with self.assertRaises(SummonError):self.s.summon('49','secondary')
  self.assertEqual(self.s.player.data,before);self.assertEqual(self.s.save_path.read_bytes(),saved)
 def test_unsupported_and_stale_offer_rejected_before_roll(self):
  before=copy.deepcopy(self.s.player.data)
  with patch.object(self.s.player,'roll_gacha',side_effect=AssertionError('roll')):
   for uid,offer in [('1','primary'),('49','stale'),('no','primary'),('9200023','primary')]:
    with self.assertRaises(SummonError):self.s.summon(uid,offer)
  self.assertEqual(self.s.player.data,before)
  q=self.s.quote('9200023');self.assertEqual(q['cost'],{'kind':'item','item_id':1209001902,'amount':10});self.assertFalse(q['supported'])
 def test_step_ticket_state_read_without_creating_keys(self):
  b=next(r for r in self.s._definitions().values() if r.get('steps'));uid=str(b['id']);sid=str(b.get('state_id',uid));self.s.player.data['gacha']['step']={sid:1};self.s.player.data['gacha']['completed_laps']={sid:2}
  before=copy.deepcopy(self.s.player.data);q=self.s.quote(uid)
  self.assertEqual((q['step'],q['lap']),(2,3));self.assertFalse(q['eligible']);self.assertEqual(before,self.s.player.data)
  b=self.s._definitions()['9100203'];b['ticket_group_id']='fixture'
  with patch.object(self.s.engine,'_load_ndjson',return_value={'__rows__':[{'zF6QIY2r':'fixture','89EvGKHx':23,'tL6G9egd':123,'zJ1A6HXm':456}]}):
   self.s.player.data.setdefault('inventory',{})['items']=[{'item_type':23,'item_id':123,'count':7}]
   before=copy.deepcopy(self.s.player.data);self.assertEqual(self.s._tickets(b)[0]['balance'],7);self.assertEqual(before,self.s.player.data)
 def test_explicit_tier_rarity_upstream_correction(self):
  with patch.object(self.s.engine,'unit_roots_by_rarity',return_value={}),patch.object(self.s.engine,'unit_mst',return_value={'9fW0TePj':7}),patch.object(self.s.engine,'_only_named',side_effect=lambda x:x):
   r=self.s.engine.expand_pool({'pool':{'tiers':[{'rarity':5,'rate':1,'units':['100000107']}]}})
  self.assertEqual(int(r[0]['rarity']),7);self.assertEqual(r[0]['rate'],1)
 def test_step_specific_pool_upstream_correction(self):
  b=copy.deepcopy(self.s.catalogue['49']);original=b['pool'];b['steps']=[{'pool':original,'cost':{'kind':'free','amount':0},'draws':1}]
  b['pool']=[]
  r=self.s.player.roll_gacha(b);self.assertIsNotNone(r);self.assertEqual(len(r['awards']),1)
 def test_rollback_and_quotes_after_save_failure(self):
  before=copy.deepcopy(self.s.player.data);saved=self.s.save_path.read_bytes()
  with patch.object(self.s.player,'save',return_value=False):
   with self.assertRaises(SummonError):self.s.summon('49')
  self.assertEqual(self.s.player.data,before);self.assertEqual(self.s.save_path.read_bytes(),saved);self.assertEqual(self.s.quote('49')['balance'],10000)
 def test_safe_area_content_width_scaling_and_touch_bounds(self):
  with tempfile.TemporaryDirectory(dir=self.root) as tmp:
   tmp=Path(tmp);main=tmp/'main.swift'
   main.write_text('import Foundation\nfor w in [320.0,375.0,390.0,393.0,402.0,440.0,768.0] { let m=GlobalMenuMetrics(width:w); precondition(m.tabHeight>=44); precondition(m.bannerWidth<=w); precondition(608*m.scale<=w); precondition(m.scale<=1); print(w,m.scale,m.tabHeight) }')
   subprocess.run(['xcrun','swiftc','-module-cache-path',str(IOS/'.local/swift-cache'),str(IOS/'native/FFBERevival/GlobalMenuMetrics.swift'),str(main),'-o',str(tmp/'metrics')],check=True,capture_output=True)
   subprocess.run([str(tmp/'metrics')],check=True,capture_output=True)
 def test_usage_caps_and_ticket_only_labels(self):
  b=self.s.catalogue['49'];b['purchase_limit']=1
  self.s.summon('49');self.assertFalse(self.s.quote('49')['eligible'])
  self.assertIn('limit',self.s.quote('49')['reason'])
  b=next(r for r in self.s._definitions().values() if r.get('ticket_group_id') and not r.get('cost') and not r.get('steps'))
  q=self.s.quote(str(b['id']));self.assertEqual(q['cost']['kind'],'ticket');self.assertFalse(q['eligible'])
 def test_resources_and_exact_mapping_reproducible_corruption(self):
  import import_global_menu as ui,import_menu_art as art
  ui.verify();art.verify();first=(art.output()/'receipt.json').read_bytes();art.run();self.assertEqual(first,(art.output()/'receipt.json').read_bytes())
  lock=json.loads(art.LOCK.read_text());keys=[(r['banner_id'],r['role']) for r in lock['artwork']];self.assertEqual(len(keys),len(set(keys)))
  for uid in ['49','9100203']:self.assertIn((uid,'banner'),keys)
  with tempfile.TemporaryDirectory(dir=self.root) as tmp:
   import shutil
   target=Path(tmp)/'art';shutil.copytree(art.output(),target);(target/'catalog.json').write_text('broken')
   with self.assertRaises(ValueError):art.verify(target)
   (target/'catalog.json').write_bytes((art.output()/'catalog.json').read_bytes())
   next((target/'images').glob('*.png')).write_bytes(b'corrupted PNG')
   with self.assertRaises(ValueError):art.verify(target)
  layout=json.loads((ui.output()/'catalog.json').read_text());self.assertEqual(layout['layouts']['top']['common_banner']['y'],338)
  self.assertTrue(all('tab-'+t+'-2' in layout['assets'] for t in ['pay','free','limited']))
if __name__=='__main__':unittest.main()

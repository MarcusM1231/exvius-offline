import sys,json,copy,tempfile,itertools,collections,unittest,math
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1];sys.path[:0]=[str(IOS/'prototype'),str(IOS/'content_tools')]
from summon_rates import normalize,distribution,details
import build_summon_catalog as content
from banner_menu import MenuSummonService
class RateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);cls.s=MenuSummonService(content.output(),Path(cls.tmp.name)/'campaign.json',demo=True,initial_lapis=100000);cls.e=cls.s.engine
 def test_all_248_banners_488_offers_exact_normalization_and_membership(self):
  report=json.loads((IOS/'.local/phase7d/rates/audit.json').read_text());self.assertEqual(len(report['records']),248);self.assertEqual(sum(len(b['offers']) for b in report['records']),488)
  for b in report['records']:
   for o in b['offers']:
    self.assertNotIn('error',o);self.assertFalse(o['discrepancies']);self.assertAlmostEqual(sum(r['expected_count'] for r in o['rows']),o['draws']);self.assertAlmostEqual(sum(r['base_probability'] for r in o['rows']),1)
    self.assertEqual(len(o['rows']),len({r['unit_id'] for r in o['rows']}))
    for r in o['rows']:self.assertTrue(0<=r['at_least_one']<=1);self.assertGreaterEqual(r['expected_count'],-1e-12)
    self.assertTrue(all(r['eligible'] and not r['historically_verified'] for r in o['featured']))
 def test_exact_distribution_matches_exhaustive_real_engine_guaranteed_draws(self):
  # Enumerate every RNG branch of a small real-engine fixture, not a sample.
  ids=['100004203','100004604','100005805'];weights=[.6,.3,.1];midpoints=[.3,.75,.95]
  for guarantee in [{'rarity':4},{'rarity':4,'count':1}]:
   b={'id':'rate-fixture','name':'Isolated rate fixture','cost':{'kind':'free','amount':0},'draws':2,'pool':[{'unit_id':u,'rarity':r,'rate':p} for u,r,p in zip(ids,[3,4,5],weights)],'guarantee':guarantee};analytic=distribution(b,{},self.e);counts=collections.Counter();seen=collections.Counter();original=copy.deepcopy(self.s.player.data)
   for indices in itertools.product(range(3),repeat=2):
    basep=math.prod(weights[i] for i in indices);replace='count' in guarantee or all(i==0 for i in indices)
    branches=[(1,.75),(2,.25)] if replace else [(1,1)]
    for replacement,conditional in branches:
     self.s.player.data=copy.deepcopy(original);self.s.player.dirty=False
     with patch.object(self.e.random,'random',side_effect=[midpoints[i] for i in indices]),patch.object(self.e.random,'choices',return_value=[b['pool'][replacement]]):result=self.s.player.roll_gacha(b)
     got=[a['unit_id'] for a in result['awards']];prob=basep*conditional
     for uid in ids:counts[uid]+=got.count(uid)*prob;seen[uid]+=(uid in got)*prob
   self.s.player.data=original
   for r in analytic['rows']:self.assertAlmostEqual(r['expected_count'],counts[r['unit_id']]);self.assertAlmostEqual(r['at_least_one'],seen[r['unit_id']])
 def test_featured_explicit_weights_boosts_and_correct_form(self):
  b=self.s.catalogue['12'];r=details(b,{},self.e);self.assertEqual({f['unit_id'] for f in r['featured']},{'100004604','204001403','206001703'})
  self.assertTrue(all(f['boosted'] for f in r['featured']));self.assertTrue(all(f['comparison_basis'].startswith('equal weight') for f in r['featured']))
  multi=details(b,b['secondary_offer'],self.e);chizuru=next(f for f in multi['featured'] if f['unit_id']=='100004604');self.assertAlmostEqual(chizuru['at_least_one'],1)
 def test_read_only_rate_query_no_rng_or_save(self):
  before=copy.deepcopy(self.s.player.data);raw=self.s.save_path.read_bytes()
  with patch.object(self.e.random,'random',side_effect=AssertionError('RNG')),patch.object(self.s.player,'save',side_effect=AssertionError('save')):self.s.menu();self.s.menu()
  self.assertEqual(self.s.player.data,before);self.assertEqual(self.s.save_path.read_bytes(),raw)
 def test_invalid_and_unmodelled_distribution_fails_clearly(self):
  with self.assertRaises(ValueError):normalize([])
  b={'pool':[{'unit_id':'100004203','rarity':3,'rate':1}],'draws':1,'guarantee':{'unit_id':'100004203'}}
  with self.assertRaisesRegex(ValueError,'separate analytic model'):distribution(b,{},self.e)
if __name__=='__main__':unittest.main()

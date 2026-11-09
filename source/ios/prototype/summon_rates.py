"""Read-only analytic projection of the existing PlayerState weighted/guaranteed draws.
Not an RNG. Probabilities are offline configuration, never historical-rate attestation.
"""
import collections,copy,math

def normalize(rows):
 total=sum(max(0,float(r.get('rate',0))) for r in rows)
 if not math.isfinite(total) or total<=0:raise ValueError('Invalid rate pool')
 result={}
 for r in rows:
  key=(str(r['unit_id']),int(r.get('rarity') or 0));result[key]=result.get(key,0)+max(0,float(r.get('rate',0)))/total
 return result

def featured_ids(b):
 out=set(str(u) for u in (b.get('community') or {}).get('unit_ids',[]))
 for definition in [b.get('pool')]+[s.get('pool') for s in b.get('steps',[])]+[(b.get('secondary_offer') or {}).get('pool')]:
  if isinstance(definition,dict):
   for tier in definition.get('tiers',[]):out.update(str(u) for u in tier.get('featured',[]))
 return sorted(out)

def distribution(b,offer,engine):
 # PlayerState uses step pools, otherwise the banner pool; offer.pool is not read.
 # Report this explicitly rather than silently pretending a configured override applies.
 step={};pool=normalize(engine.expand_pool(b));n=int((offer.get('cost') or b.get('cost') or {}).get('draws') or offer.get('draws') or b.get('draws',1));g=offer.get('guarantee') or b.get('guarantee') or {};extras=b.get('guarantee_slots',[])
 if not 1<=n<=11:raise ValueError('Unsupported draw count')
 if g.get('any_of') or g.get('unit_id'):raise ValueError('Combined fixed-unit guarantees need a separate analytic model')
 slots=[pool.copy() for _ in range(n)];reserved=sum(int(s.get('count',1)) for s in extras)
 if 'count' in g and g.get('rarity') is not None:
  candidates=engine.expand_pool({'pool':g['pool']}) if g.get('pool') is not None else engine.expand_pool(b)
  gp=normalize([r for r in candidates if int(r.get('rarity') or 0)>=int(g['rarity'])]);count=int(g['count'])
  for i in range(n-reserved-count,n-reserved):slots[i]=gp
 cursor=n-reserved
 for s in extras:
  sp=normalize(engine.expand_pool({'pool':s['pool']}))
  for i in range(cursor,cursor+int(s.get('count',1))):slots[i]=sp
  cursor+=int(s.get('count',1))
 keys=set().union(*slots);expected={k:sum(s.get(k,0) for s in slots) for k in keys};atleast={k:1-math.prod(1-s.get(k,0) for s in slots) for k in keys};mode='independent slots'
 if g.get('rarity') is not None and 'count' not in g:
  if extras:raise ValueError('Conditional guarantee plus extra slots needs a separate analytic model')
  floor=int(g['rarity']);low={k:p for k,p in pool.items() if k[1]<floor};high={k:p for k,p in pool.items() if k[1]>=floor};h=sum(high.values());lowtotal=sum(low.values())
  if not h:raise ValueError('Empty guaranteed rarity')
  # Legacy engine replaces the first minimum-rarity draw only when all miss floor.
  for k,p in high.items():expected[k]+=lowtotal**n*p/h;atleast[k]+=lowtotal**n*p/h
  for k,p in low.items():
   above=sum(v for j,v in low.items() if j[1]>k[1]);ge=sum(v for j,v in low.items() if j[1]>=k[1]);expected[k]-=p*sum(above**i*ge**(n-1-i) for i in range(n));atleast[k]-=p*sum(above**i*(ge-p)**(n-1-i) for i in range(n))
  mode='conditional first-minimum replacement'
 assert abs(sum(expected.values())-n)<1e-8
 rows=[{'unit_id':k[0],'rarity':k[1],'base_probability':pool.get(k,0),'expected_count':expected[k],'per_draw_average':expected[k]/n,'at_least_one':max(0,min(1,atleast[k]))} for k in sorted(keys)]
 return {'draws':n,'guarantee':copy.deepcopy(g),'guarantee_slots':copy.deepcopy(extras),'model':mode,'base_weight_total':sum(float(r['rate']) for r in engine.expand_pool(b)),'rows':rows}

def details(b,offer,engine):
 result=distribution(b,offer,engine);ids=featured_ids(b);base=normalize(engine.expand_pool(b));mass=collections.defaultdict(float);counts=collections.Counter(k[1] for k in base)
 for k,v in base.items():mass[k[1]]+=v
 # An explicit row pool has no removable featured-share switch. Use a clearly
 # defined counterfactual: equal weight among the SAME eligible forms in each
 # awarded-rarity tier, retaining that tier's actual total probability.
 baseline={k:mass[k[1]]/counts[k[1]] for k in base};featured=[]
 for uid in ids:
  rows=[r for r in result['rows'] if r['unit_id']==uid];master=engine.unit_mst(uid) or {};actual=sum(r['base_probability'] for r in rows);comparison=sum(v for k,v in baseline.items() if k[0]==uid)
  explicit=[]
  if isinstance(b.get('pool'),dict):
   explicit=[{'tier_rarity':t.get('rarity'),'tier_weight':t.get('rate'),'featured_share':t.get('featured_share',0)} for t in b['pool'].get('tiers',[]) if uid in [str(v) for v in t.get('featured',[])]]
  implicit=uid in [str(v) for v in (b.get('community') or {}).get('unit_ids',[])] and isinstance(b.get('pool'),dict) and not any(t.get('featured') for t in b['pool'].get('tiers',[]))
  featured.append({'unit_id':uid,'name':engine.unit_name(uid) if hasattr(engine,'unit_name') else uid,'rarity':int(master.get('9fW0TePj') or 0),'eligible':bool(rows),'explicit_featured_tiers':explicit,'implicit_community_top_tier_share':0.5 if implicit else None,'configured_raw_weight':actual*result['base_weight_total'],'base_probability':actual,'equal_weight_probability':comparison,'comparison_basis':'equal weight within the same eligible awarded-rarity tier','configuration_kind':'explicit row weights' if isinstance(b.get('pool'),list) else 'tier weights / featured share','boosted':actual>comparison+1e-12,'expected_count':sum(r['expected_count'] for r in rows),'per_draw_average':sum(r['per_draw_average'] for r in rows),'at_least_one':sum(r['at_least_one'] for r in rows),'historically_verified':False})
 result['featured']=featured;return result

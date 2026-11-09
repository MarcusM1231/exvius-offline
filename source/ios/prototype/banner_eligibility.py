"""Conservative pure preflight of existing engine definitions. Never chooses rewards."""
import copy,hashlib,json,math

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def referenced_units(v):
 result=set()
 if isinstance(v,dict):
  if 'unit_id' in v:result.add(str(v['unit_id']))
  for k in ('units','featured','any_of'):
   if isinstance(v.get(k),list):result.update(str(x) for x in v[k] if isinstance(x,(str,int)))
  for x in v.values():result.update(referenced_units(x))
 elif isinstance(v,list):
  for x in v:result.update(referenced_units(x))
 return result

def audit(b,engine,named):
 errors=[];steps=b.get('steps') or []
 if b.get('boxes') or b.get('selection'):errors.append('Box/selection requires its own request and result screen.')
 if any(b.get(k) for k in ('reward_pool','bonus_rewards','bonus_choice','milestone_bonus')):errors.append('Additional rewards require a validated mixed-reward presentation.')
 variants=[('step-'+str(i+1),s) for i,s in enumerate(steps)] if steps else [('primary',{})]+([('secondary',b['secondary_offer'])] if b.get('secondary_offer') else [])
 pools={};offers=[];required=set()
 def check_units(pool,label):
  if not pool:errors.append(label+': empty pool');return
  for r in pool:
   uid=str(r.get('unit_id',''));required.add(uid)
   master=engine.unit_mst(uid)
   if not master or uid not in named:errors.append(label+': missing unit/name '+uid)
   if master and int(master.get('9fW0TePj',0))>=7:errors.append('Rarity-7/NV rewards need verified Vision Card metadata and reward presentation.')
   w=float(r.get('rate',0))
   if not math.isfinite(w) or w<=0:errors.append(label+': invalid weight')
  if sum(float(r.get('rate',0)) for r in pool)<=0:errors.append(label+': no positive probability')
 for kind,s in variants:
  if any(s.get(k) for k in ('bonus_rewards','bonus_choice','reward_pool','milestone_bonus')):errors.append(kind+': bonus rewards are not supported')
  cost=s.get('cost',b.get('cost'))
  if not isinstance(cost,dict) or cost.get('kind') not in ('lapis','lapis_free','lapis_paid','gil','friend_point','free'):
   errors.append(kind+': ticket/item purchase adapter is not enabled');continue
  amount=cost.get('amount',0)
  if isinstance(amount,bool) or not isinstance(amount,int) or amount<0:errors.append(kind+': invalid cost')
  if cost.get('kind')!='free' and amount<=0:errors.append(kind+': missing positive cost')
  draws=int(cost.get('draws') or s.get('draws') or b.get('draws',1))
  if not 1<=draws<=11:errors.append(kind+': unsupported draw count')
  pool_definition=s.get('pool',b.get('pool'))
  all_refs=referenced_units(pool_definition)|referenced_units(s.get('guarantee',b.get('guarantee',{})))|referenced_units(s.get('guarantee_slots',b.get('guarantee_slots',[])))
  missing=sorted(u for u in all_refs if not engine.unit_mst(u) or u not in named)
  if missing:errors.append(kind+': missing explicitly referenced unit metadata: '+','.join(missing))
  expanded=engine.expand_pool(dict(b,pool=pool_definition));check_units(expanded,kind);pools[kind]=digest(expanded)
  # Never normalize away a wholly absent positive tier.
  if isinstance(pool_definition,dict):
   roots=engine.unit_roots_by_rarity()
   for t in pool_definition.get('tiers',[]):
    if float(t.get('rate',0))>0 and not t.get('units') and not roots.get(str(t.get('rarity'))) and not t.get('featured'):errors.append(kind+': missing positive rarity tier '+str(t.get('rarity')))
  g=s.get('guarantee') or b.get('guarantee') or {};slots=s.get('guarantee_slots',b.get('guarantee_slots',[]));reserved=0
  for i,slot in enumerate(slots):
   sp=engine.expand_pool({'pool':slot.get('pool')});check_units(sp,kind+' guaranteed slot');reserved+=int(slot.get('count',1))
   if int(slot.get('count',1))<1:errors.append(kind+': invalid guaranteed slot count')
  gp=engine.expand_pool({'pool':g['pool']}) if g.get('pool') is not None else expanded
  if g.get('pool') is not None:check_units(gp,kind+' guarantee pool')
  if g.get('rarity') is not None and not any(int(r.get('rarity') or 0)>=int(g['rarity']) for r in gp):errors.append(kind+': guaranteed rarity unavailable')
  count=int(g.get('count',1)) if g else 0
  if count<0 or reserved+count>draws:errors.append(kind+': guaranteed slots exceed draw count')
  offers.append({'offer':kind,'draws':draws,'cost':copy.deepcopy(cost),'guarantee':copy.deepcopy(g),'pool_sha256':pools[kind],'pool_rows':len(expanded)})
 return {'id':str(b['id']),'name':b.get('name'),'definition_sha256':digest(b),'eligible':not errors,'reasons':sorted(set(errors)),'offers':offers,'required_units':sorted(required),'step_count':len(steps)}

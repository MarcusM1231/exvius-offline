"""Audit every enabled offer from pinned existing Python definitions; no campaign purchases."""
import json,sys,tempfile,collections
from pathlib import Path
from import_content import IOS
sys.path.insert(0,str(IOS/'prototype'))
from build_summon_catalog import output
from banner_menu import MenuSummonService
from summon_rates import details,featured_ids
ROOT=IOS/'.local/phase7d/rates'
def run():
 ROOT.mkdir(parents=True,exist_ok=True)
 sources=collections.defaultdict(set)
 def walk(v,path):
  if isinstance(v,dict):
   if 'id' in v and 'pool' in v:sources[str(v['id'])].add(path)
   for x in v.values():walk(x,path)
  elif isinstance(v,list):
   for x in v:walk(x,path)
 for p in (IOS.parent/'server').glob('gacha_*.json'):walk(json.loads(p.read_text()),str(p.relative_to(IOS.parent)))
 with tempfile.TemporaryDirectory() as tmp:
  service=MenuSummonService(output(),Path(tmp)/'research.json',demo=True);records=[]
  for uid,b in sorted(service.catalogue.items(),key=lambda kv:int(kv[0])):
   variants=[('primary',{})]+([('secondary',b['secondary_offer'])] if b.get('secondary_offer') else []);offers=[]
   for name,o in variants:
    try:
     d=details(b,o,service.engine)
     for r in d['featured']:r['name']=service.gacha.unit_name(r['unit_id']) or r['unit_id']
     d['offer']=name;d['discrepancies']=[]
     if o.get('pool') and o['pool']!=b.get('pool'):d['discrepancies'].append('Configured offer.pool is ignored by legacy PlayerState; actual banner pool shown')
     if o.get('guarantee_slots') and o['guarantee_slots']!=b.get('guarantee_slots'):d['discrepancies'].append('Configured offer.guarantee_slots ignored by legacy PlayerState')
     missing=[r['unit_id'] for r in d['featured'] if not r['eligible']]
     if missing:d['discrepancies'].append('Featured metadata IDs absent from actual pool: '+','.join(missing))
     offers.append(d)
    except ValueError as error:offers.append({'offer':name,'error':str(error)})
   records.append({'id':uid,'name':b['name'],'definition_files':sorted(sources[uid]),'definition_source':b.get('source') or b.get('rate_source'),'community_evidence':b.get('community'),'configured_pool':b.get('pool'),'offers':offers})
 report={'schema':1,'scope':'Actual configured Python probabilities; not original server odds. Artwork alone does not prove pool membership.','records':records};(ROOT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'banners':len(records),'offers':sum(len(r['offers']) for r in records),'errors':[(r['id'],o) for r in records for o in r['offers'] if o.get('error')],'discrepancies':[(r['id'],o['offer'],o.get('discrepancies')) for r in records for o in r['offers'] if o.get('discrepancies')]}),flush=True);return report
if __name__=='__main__':run()

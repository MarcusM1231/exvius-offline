"""Cache-only full summon metadata + exhaustive real-engine validation in a fresh process."""
import copy,hashlib,json,os,sys,tempfile,shutil,subprocess
from pathlib import Path
from import_content import IOS,sha,load_lock,validate_source,DEFAULT_SOURCE
ROOT=IOS/'.local/phase7c/catalog';LOCK=Path(__file__).with_name('summon-catalog.lock.json')

def prepare():
 from demo_data import prepare as demo
 ROOT.mkdir(parents=True,exist_ok=True);stage=ROOT/'metadata-stage'
 if stage.exists():
  # This is a task-owned generated staging root, never a campaign directory.
  assert (stage/'synthetic-metadata.json').is_file()
 demo(stage)
 for e in load_lock()['members']:
  if e['name'].endswith('.ndjson'):
   p=DEFAULT_SOURCE/e['name'];validate_source(p.read_bytes(),e)
   target=stage/e['name'].removeprefix('static/');shutil.copy2(p,target)
 for r in json.loads(Path(__file__).with_name('summon-masters.lock.json').read_text())['sources']:
  p=IOS/r['cache_path'];validate_source(p.read_bytes(),r['entry']);shutil.copy2(p,stage/'mst_decoded'/p.name)
 return stage

def run():
 sys.path.insert(0,str(IOS/'prototype'));data=prepare()
 os.environ.update(FFBE_DATA=str(data),MST_DIR=str(data/'mst_decoded'),TEXT_DIR=str(data/'text_decoded'),GACHA_ONLY='all',GACHA_CAMPAIGN='all',GACHA_STANDARD='1')
 sys.path.insert(0,str(IOS.parent/'server'))
 import player_state as engine,ffbe_gacha,gacha_archive
 from banner_eligibility import audit,digest
 named=engine.named_unit_ids();banners={str(b['id']):b for b in ffbe_gacha.all_banners()};groups=gacha_archive.catalogue(list(banners.values()));visible={uid for g in groups for uid in g['ids']}|{'49','9100203'}
 # These two remain authored definitions even where an archive alias exists.
 banners.update({str(b['id']):b for b in ffbe_gacha.authored_banners() if str(b['id']) in ('49','9100203')})
 if '9200023' in banners:banners['9200023']=dict(banners['9200023'],cost={'kind':'item','item_id':1209001902,'amount':10})
 results=[];enabled={};base=engine.PlayerState.load(str(ROOT/'unused-validation-campaign.json'),slot='catalog-validation',mode='live')
 base.add_currency('lapis_free',100000000);base.add_currency('gil',100000000);base.add_currency('friend_point',100000000)
 initial=copy.deepcopy(base.data)
 for uid in sorted(visible,key=int):
  b=banners[uid];r=audit(b,engine,named);r['type']=b.get('type');r['art']=b.get('art');r['definition_source']=b.get('source') or b.get('rate_source')
  if r['eligible']:
   for o in r['offers']:
    base.data=copy.deepcopy(initial);base.dirty=False
    if o['offer'].startswith('step-'):base.data['gacha']['step'][str(b.get('state_id',uid))]=int(o['offer'][5:])-1;offer=None
    else:offer=b.get('secondary_offer') if o['offer']=='secondary' else None
    try:
     before=copy.deepcopy(base.data);result=base.roll_gacha(copy.deepcopy(b),offer=copy.deepcopy(offer))
     assert result and len(result['awards'])==o['draws'] and not result.get('nv_cards') and not result.get('bonus_awards') and not result.get('reward_awards'),'Result shape/reward type'
     assert all(a['instance_id'] and engine.unit_mst(a['unit_id']) and a['unit_id'] in named for a in result['awards']),'Invalid unit serialization'
     currency=o['cost']['kind'];amount=int(o['cost'].get('amount',0));beforec=before['currencies'];afterc=base.data['currencies']
     if currency=='lapis':assert beforec['lapis_free']+beforec['lapis_paid']-afterc['lapis_free']-afterc['lapis_paid']==amount,'Wrong charge'
     elif currency!='free':assert beforec.get(currency,0)-afterc.get(currency,0)==amount,'Wrong currency charge'
     if b.get('steps'):
      sid=str(b.get('state_id',uid));i=int(o['offer'][5:])-1;assert base.data['gacha']['step'][sid]==(i+1)%len(b['steps']),'Step progression'
     with tempfile.TemporaryDirectory(prefix='ffbe-catalog-transaction-') as temp:
      save=Path(temp)/'test.json';assert base.save(str(save));restored=engine.PlayerState.load(str(save),slot='catalog-validation',mode='live')
      assert restored.data['roster']==base.data['roster'] and restored.data['currencies']==base.data['currencies'] and restored.data['gacha']==base.data['gacha'],'Save/reload changed rewards'
     o['transaction_and_reload']='passed'
    except Exception as error:r['eligible']=False;r['reasons'].append(o['offer']+': real engine validation failed: '+str(error));break
  if r['eligible']:enabled[uid]=r['definition_sha256']
  results.append(r)
 policy={'schema':1,'scope':'Only source-pinned banners passing full metadata, unit-only rewards and real engine/save validation','enabled':enabled,'engine_sha256':sha((IOS.parent/'server/player_state.py').read_bytes()),'reasons':{r['id']:r['reasons'] for r in results if not r['eligible']}}
 (data/'catalog-policy.json').write_text(json.dumps(policy,sort_keys=True,indent=2)+'\n')
 source_pins={str(p.relative_to(IOS)):sha(p.read_bytes()) for p in [Path(__file__),IOS/'prototype/banner_eligibility.py',IOS/'content_tools/content.lock.json',IOS/'content_tools/summon-masters.lock.json']}
 lock={'schema':1,'policy_sha256':sha((data/'catalog-policy.json').read_bytes()),'files':{str(p.relative_to(data)):sha(p.read_bytes()) for p in sorted(data.rglob('*')) if p.is_file()},'source_pins':source_pins,'enabled_ids':sorted(enabled,key=int),'master_rows':len(engine._load_ndjson('F_UNIT_MST.ndjson')['__rows__']),'named_ids':len(named)}
 body=json.dumps(lock,indent=2)+'\n'
 if LOCK.exists() and LOCK.read_text()!=body:raise ValueError('Audited catalog lock changed; review before updating')
 if not LOCK.exists():LOCK.write_text(body)
 dest=output();dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():shutil.copytree(data,dest)
 verify();(ROOT/'eligibility.json').write_text(json.dumps({'records':results,'enabled_ids':sorted(enabled,key=int),'metadata':{'master_rows':lock['master_rows'],'named_ids':lock['named_ids']}},indent=2)+'\n')
 print(json.dumps({'entries':len(results),'enabled':len(enabled),'steps':sum(bool(r['step_count']) and r['eligible'] for r in results),'reasons':__import__('collections').Counter(reason for r in results for reason in r['reasons']),'root':str(dest)}),flush=True)

def output():return ROOT/'versions'/sha(LOCK.read_bytes())[:16]/'metadata'
def verify(root=None):
 root=Path(root or output());lock=json.loads(LOCK.read_text())
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 if actual!=set(lock['files']):raise ValueError('Catalog metadata file set')
 for name,digest in lock['files'].items():
  if sha((root/name).read_bytes())!=digest:raise ValueError('Catalog metadata checksum: '+name)
 for name,digest in lock['source_pins'].items():
  if sha((IOS/name).read_bytes())!=digest:raise ValueError('Catalog audit source changed: '+name)
if __name__=='__main__':run()

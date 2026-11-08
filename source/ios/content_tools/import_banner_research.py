"""Versioned optional read-only research snapshot; never changes production catalog/rules."""
import json,shutil,tempfile
from pathlib import Path
from import_content import IOS,sha
from banner_catalogue import snapshot,canonical
ART_LOCK=Path(__file__).with_name('banner-research-art.lock.json')
LOCK=Path(__file__).with_name('banner-research.lock.json')
ROOT=IOS/'.local/phase7a'
def output():return ROOT/'versions'/sha(LOCK.read_bytes())[:16]/'BannerResearch'
def price(offer,ticket_group=None):
 c=offer.get('cost')
 if isinstance(c,list):return 'Multiple cost entries; Python quote required'
 if isinstance(c,dict) and c.get('amount'):return f"{c['amount']} {c.get('kind','unknown')}"+(f" · item {c['item_id']}" if c.get('item_id') else '')
 return f'Ticket group {ticket_group}; Python quote required' if ticket_group else 'Free (definition)'
def build():
 result=snapshot();art=json.loads(ART_LOCK.read_text());ROOT.mkdir(exist_ok=True)
 # Persist the full audit separately; only a compact presentation projection ships.
 (ROOT/'banner-catalogue.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 records=[]
 for r in result['records']:
  images=[{'role':a['role'],'file':f"images/{r['id']}-{a['role']}.png",'width':a['width'],'height':a['height'],'provenance':a['provenance']} for a in r['artwork']]
  offers=[{'label':('Step '+str(o['step'])) if 'step' in o else o['kind'].title(),'draws':int(o['draws']),'price':price(o,r['ticket_group_id']),'guarantee':json.dumps(o.get('guarantee') or {},ensure_ascii=False)[:400]} for o in r['offers']]
  records.append({'id':r['id'],'name':r['name'],'tab':r['global_tab'],'groups':r['archive_groups'],'visible':r['visible_in_archive'],'images':images,'offers':offers,'featured':r['featured_unit_ids'][:12],'source':', '.join(x['file'].split('/')[-1] for x in r['source_definitions']),'notice':r['rate_notice'] or 'Pools and rates are repository definitions, not recovered original-server odds.','issues':r['known_issues'],'ios_status':r['ios_integration']})
 data=(canonical({'schema':1,'read_only':True,'groups':[{'id':r['id'],'label':r['label']} for r in result['groups']],'records':records})+'\n').encode()
 lock={'schema':1,'scope':'Developer-only read-only snapshot; no campaign/player/RNG access','source_hashes':result['source_hashes'],'art_lock_sha256':sha(ART_LOCK.read_bytes()),'presentation_catalog_sha256':sha(data),'record_count':len(records)}
 text=json.dumps(lock,indent=2)+'\n'
 if LOCK.exists() and LOCK.read_text()!=text:raise ValueError('Research snapshot sources changed; review before updating lock')
 if not LOCK.exists():LOCK.write_text(text)
 dest=output();dest.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
  root=Path(tmp)/'BannerResearch';root.mkdir();(root/'catalog.json').write_bytes(data)
  for a in art['artwork']:
   raw=(IOS/a['cache_path']).read_bytes()
   if sha(raw)!=a['entry']['sha256']:raise ValueError('Research art source changed')
   p=root/f"images/{a['banner_id']}-{a['role']}.png";p.parent.mkdir(exist_ok=True);p.write_bytes(raw)
  receipt={'lock_sha256':sha(LOCK.read_bytes()),'files':{str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}}
  (root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
  if dest.exists():
   if (dest/'receipt.json').read_bytes()!=(root/'receipt.json').read_bytes():raise ValueError('Existing research output differs')
  else:shutil.copytree(root,dest)
 verify();return {'records':len(records),'verified_images':len(art['artwork']),'catalog_bytes':len(data),'bundle_bytes':sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()),'root':str(dest)}
def verify(root=None):
 root=Path(root or output());lock=json.loads(LOCK.read_text());r=json.loads((root/'receipt.json').read_text())
 if r['lock_sha256']!=sha(LOCK.read_bytes()) or sha(ART_LOCK.read_bytes())!=lock['art_lock_sha256']:raise ValueError('Research lock identity')
 repo=IOS.parent.parent
 for name,digest in lock['source_hashes'].items():
  if sha((repo/name).read_bytes())!=digest:raise ValueError('Stale research snapshot source: '+name)
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}-{'receipt.json'}
 if actual!=set(r['files']):raise ValueError('Research bundle file set')
 for name,digest in r['files'].items():
  if sha((root/name).read_bytes())!=digest:raise ValueError('Research output checksum')
 if sha((root/'catalog.json').read_bytes())!=lock['presentation_catalog_sha256']:raise ValueError('Research catalog identity')
if __name__=='__main__':print(json.dumps(build()))

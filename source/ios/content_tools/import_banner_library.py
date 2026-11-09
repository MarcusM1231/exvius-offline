"""Exact-ID atlas-free library with content-addressed deduplication and strict receipts."""
import json,tempfile,shutil
from pathlib import Path
from import_content import IOS,sha
from recover_banner_library import validate
LOCK=Path(__file__).with_name('banner-library.lock.json')
def output():return IOS/'.local/phase7c/artwork/versions'/sha(LOCK.read_bytes())[:16]/'BannerArt'
def verify(root=None):
 root=Path(root or output());r=json.loads((root/'receipt.json').read_text())
 if r['lock_sha256']!=sha(LOCK.read_bytes()):raise ValueError('Banner library lock')
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}-{'receipt.json'}
 if actual!=set(r['files']):raise ValueError('Banner library file set')
 for name,digest in r['files'].items():
  if sha((root/name).read_bytes())!=digest:raise ValueError('Banner library corrupt output: '+name)
 return r

def run():
 lock=json.loads(LOCK.read_text())
 if len({r['key'] for r in lock['artwork']})!=len(lock['artwork']):raise ValueError('Duplicate source identity')
 dest=output();dest.parent.mkdir(parents=True,exist_ok=True);catalog={};extra={}
 for r in lock['artwork']:
  for m in r['mapping']:
   if m['role']=='detail_extra':extra.setdefault(m['banner_id'],[]).append(r['entry']['name'])
 for uid in extra:extra[uid]=sorted(set(extra[uid]))
 with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
  root=Path(tmp)/'BannerArt';(root/'images').mkdir(parents=True);logical=0;input_bytes=0
  for r in lock['artwork']:
   raw=(IOS/r['cache_path']).read_bytes()
   if sha(raw)!=r['sha256']:raise ValueError('Banner source pin')
   if list(validate(raw,r['entry']))!=[r['width'],r['height']]:raise ValueError('Banner dimensions changed')
   filename='images/'+r['sha256']+'.png';target=root/filename
   if not target.exists():target.write_bytes(raw)
   input_bytes+=len(raw)
   for m in r['mapping']:
    uid=m['banner_id'];role=m['role']
    if not uid.isascii() or not uid.isdecimal():raise ValueError('Invalid master banner ID')
    if role=='detail_extra':role='detail_extra_'+str(extra[uid].index(r['entry']['name']))
    if role not in ['banner','detail_banner'] and not role.startswith('detail_extra_'):raise ValueError('Unexpected art role')
    row={'file':filename,'width':r['width'],'height':r['height'],'provenance':r['provenance']}
    if role in catalog.setdefault(uid,{}) and catalog[uid][role]!=row:raise ValueError('Ambiguous exact banner ID/role '+uid+' '+role)
    catalog[uid][role]=row;logical+=1
  (root/'catalog.json').write_text(json.dumps(catalog,sort_keys=True,indent=2)+'\n')
  receipt={'lock_sha256':sha(LOCK.read_bytes()),'files':{str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}}
  (root/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
  if dest.exists():
   verify(dest)
   if (dest/'receipt.json').read_bytes()!=(root/'receipt.json').read_bytes():raise ValueError('Nondeterministic banner library')
  else:shutil.copytree(root,dest)
 verify();report={'ids':len(catalog),'source_images':len(lock['artwork']),'unique_pngs':len(list((dest/'images').glob('*.png'))),'logical_mappings':logical,'input_image_bytes':input_bytes,'bundle_bytes':sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()),'root':str(dest)}
 (IOS/'.local/phase7c/artwork/bundle-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return report
if __name__=='__main__':run()

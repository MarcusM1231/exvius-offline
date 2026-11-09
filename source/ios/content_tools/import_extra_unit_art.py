"""Three reported exact-form static gaps; no animation recovery or primary-art edits."""
import json,shutil,tempfile,argparse
from pathlib import Path
from import_content import IOS,sha,validate_png
from range_client import RangeClient
LOCK=Path(__file__).with_name('extra-unit-art.lock.json');ROOT=IOS/'.local/phase7c/extra-units'
TARGETS=['206000504','100004104','100004105']
def output():return ROOT/'versions'/sha(LOCK.read_bytes())[:16]/'ExtraUnitArt'
def verify(root=None):
 root=Path(root or output());r=json.loads((root/'receipt.json').read_text())
 if r['lock_sha256']!=sha(LOCK.read_bytes()):raise ValueError('Extra exact-form lock')
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}-{'receipt.json'}
 if actual!=set(r['files']):raise ValueError('Extra art file set')
 for name,digest in r['files'].items():
  if sha((root/name).read_bytes())!=digest:raise ValueError('Extra art checksum')
 return r

def run(download=False):
 ROOT.mkdir(parents=True,exist_ok=True)
 if LOCK.exists():lock=json.loads(LOCK.read_text())
 else:
  original=json.loads(Path(__file__).with_name('content.lock.json').read_text());rows=[]
  for uid in TARGETS:
   matches=[]
   for key,source in original['range_sources'].items():
    ip=IOS/'.local/unit-content/discovery'/(key+'.json')
    if not ip.exists():continue
    if sha(ip.read_bytes())!=source['index_sha256']:raise ValueError('Unit CPK index changed')
    idx=json.loads(ip.read_text())
    for e in idx['entries']:
     if e['name']=='unit_ills_'+uid+'.png':matches.append({'unit_id':uid,'entry':e,'source':source,'index_path':str(ip.relative_to(IOS))})
   if len(matches)!=1:raise ValueError('Missing/ambiguous exact static form '+uid)
   rows.append(matches[0])
  lock={'schema':1,'scope':'Exact original static form files, separately supplementing the immutable 423-ID library. No animation data. Global-targeted preservation, not retail CDN attestation.','artwork':rows}
 if len({r['unit_id'] for r in lock['artwork']})!=len(lock['artwork']):raise ValueError('Duplicate exact form')
 client=RangeClient(interval=1,max_bytes=65536,journal=ROOT/'ranges.json')
 for r in lock['artwork']:
  e=r['entry'];s=r['source'];p=ROOT/(r['unit_id']+'.png')
  if e['name']!='unit_ills_'+r['unit_id']+'.png' or e['size']!=e['unpacked'] or e['offset_in_cpk']+e['size']>s['cpk_size']:raise ValueError('Static form identity/bounds')
  if sha((IOS/r['index_path']).read_bytes())!=s['index_sha256']:raise ValueError('Static source index pin')
  index=json.loads((IOS/r['index_path']).read_text())
  if e not in index['entries']:raise ValueError('Static source entry mismatch')
  if not p.exists():
   if not download:raise FileNotFoundError('Run import_extra_unit_art.py --download')
   body=client.read(s,s['zip_payload_start']+e['offset_in_cpk'],e['size']);validate_png(body);p.write_bytes(body)
  body=p.read_bytes();info=validate_png(body)
  if len(body)!=e['size'] or r.get('sha256') and r['sha256']!=sha(body):raise ValueError('Static form checksum')
  r.update(sha256=sha(body),cache_path=str(p.relative_to(IOS)))
 text=json.dumps(lock,indent=2)+'\n'
 if LOCK.exists() and LOCK.read_text()!=text:raise ValueError('Pinned exact form changed')
 if not LOCK.exists():LOCK.write_text(text)
 dest=output();dest.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
  stage=Path(tmp)/'ExtraUnitArt';(stage/'sprites').mkdir(parents=True);catalog={}
  for r in lock['artwork']:
   name='sprites/'+r['unit_id']+'.png';shutil.copy2(IOS/r['cache_path'],stage/name);catalog[r['unit_id']]={'file':name,'sha256':r['sha256']}
  (stage/'catalog.json').write_text(json.dumps(catalog,sort_keys=True,indent=2)+'\n')
  receipt={'lock_sha256':sha(LOCK.read_bytes()),'files':{str(p.relative_to(stage)):sha(p.read_bytes()) for p in sorted(stage.rglob('*')) if p.is_file()}}
  (stage/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
  if dest.exists():
   verify(dest)
   if (dest/'receipt.json').read_bytes()!=(stage/'receipt.json').read_bytes():raise ValueError('Nonreproducible static forms')
  else:shutil.copytree(stage,dest)
 verify();print(json.dumps({'exact_ids':[r['unit_id'] for r in lock['artwork']],'network_bytes':client.transferred,'bundle_bytes':sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())}));return lock
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');run(p.parse_args().download)

"""Bounded, resumable exact-ID English banner batch. No full archives/runtime network."""
import copy,json,time,zlib
from pathlib import Path
from import_content import IOS,sha,download_member
from range_client import RangeClient
from png_validation import png_info
LOCK=Path(__file__).with_name('global-menu-art.lock.json')
ROOT=IOS/'.local/phase7b'
def recover():
 from PIL import Image
 ROOT.mkdir(exist_ok=True)
 if LOCK.exists():result=json.loads(LOCK.read_text())
 else:
  original=json.loads(Path(__file__).with_name('banner-research-art.lock.json').read_text())
  rows=copy.deepcopy(original['artwork']);by={str(b['id']):b for name in ['gacha_catalogue','gacha_community','gacha_named','gacha_authored','gacha_standard'] for b in json.loads((IOS.parent/'server'/f'{name}.json').read_text())['banners']}
  idxpath=IOS/'.local/phase6a/source-indexes/data-010-index.json';idx=json.loads(idxpath.read_text());entries={e['name']:e for e in idx['entries']}
  ids=['1','9','24','33','70001','60001','60002','45','11']
  ids += [uid for uid,b in sorted(by.items(),key=lambda x:int(x[0])) if b.get('type')=='step']
  ids += sorted(by,key=int)
  imported={r['banner_id'] for r in rows};count=0
  for uid in dict.fromkeys(ids):
   if uid in imported:continue
   b=by.get(uid,{})
   for role,folder in [('banner','main'),('detail_banner','sub')]:
    name=(b.get('art') or {}).get(role)
    if not isinstance(name,str):continue
    path=f'native/en/sd/static_banner/gacha/{folder}/'+name
    if path not in entries:continue
    matches={r['sha256'] for r in b.get('sources',[]) if Path(r.get('file','')).name==name and r.get('sha256')}
    if len(matches)!=1:continue
    e=dict(entries[path],archive='data-010',url=idx['url'],archive_size=idx['archive_size'],sha256=matches.pop())
    if e['size']>512000 or e['method'] not in (0,8):continue
    rows.append({'banner_id':uid,'role':role,'provenance':'global-targeted-preservation-en-static-banner','entry':e,'index_path':str(idxpath.relative_to(IOS)),'index_sha256':sha(idxpath.read_bytes()),'cache_path':str((ROOT/'sources'/uid/(role+'.png')).relative_to(IOS))})
    count+=1
   if count>=22:break
  result={'schema':1,'provenance_warning':original['provenance_warning'],'artwork':rows}
 client=RangeClient(interval=1,max_bytes=4000000,journal=ROOT/f'ranges-{time.time_ns()}.json')
 for r in result['artwork']:
  if sha((IOS/r['index_path']).read_bytes())!=r['index_sha256']:raise ValueError('ZIP index changed')
  e=r['entry'];path=IOS/r['cache_path']
  if not path.exists():download_member(e,path,client=client)
  raw=path.read_bytes()
  if sha(raw)!=e['sha256'] or len(raw)!=e['size'] or zlib.crc32(raw)!=e['crc32']:raise ValueError('Banner member identity mismatch')
  with Image.open(path) as im:
   im.load();png_info(raw,require_transparency=False,raster=im);r['width'],r['height']=im.size
 body=json.dumps(result,indent=2)+'\n'
 if LOCK.exists() and LOCK.read_text()!=body:raise ValueError('Changed locked art batch')
 if not LOCK.exists():LOCK.write_text(body)
 print(json.dumps({'images':len(result['artwork']),'ids':len({r['banner_id'] for r in result['artwork']}),'network_bytes':client.transferred}))
 return result
if __name__=='__main__':recover()

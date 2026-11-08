"""One small expansion: exact indexed permanent English art lacking prior source SHA pins.
First recovery checks pinned index/header/name/CRC/PNG, then records observed SHA-256.
Subsequent recoveries use recover_menu_art.py with the resulting complete lock.
"""
import json,struct,zlib,time
from pathlib import Path
from import_content import IOS,sha
from range_client import RangeClient
from recover_menu_art import LOCK,ROOT

def run():
 from PIL import Image
 import io
 from png_validation import png_info
 result=json.loads(LOCK.read_text());known={(r['banner_id'],r['role']) for r in result['artwork']}
 by={str(b['id']):b for f in ['gacha_authored','gacha_standard'] for b in json.loads((IOS.parent/'server'/f'{f}.json').read_text())['banners']}
 ip=IOS/'.local/phase6a/source-indexes/data-010-index.json';idx=json.loads(ip.read_text());entries={e['name']:e for e in idx['entries']}
 client=RangeClient(interval=1,max_bytes=2000000,journal=ROOT/f'permanent-ranges-{time.time_ns()}.json')
 for uid in ['1','9','24','33','70001','60001','60002','45','11']:
  for role,folder in [('banner','main'),('detail_banner','sub')]:
   if (uid,role) in known:continue
   name=by[uid].get('art',{}).get(role);path=f'native/en/sd/static_banner/gacha/{folder}/{name}'
   if path not in entries:continue
   e=dict(entries[path],archive='data-010',url=idx['url'],archive_size=idx['archive_size'])
   if max(e['size'],e['compressed'])>512000 or e['method'] not in (0,8):raise ValueError('Oversize/method')
   target=ROOT/'sources'/uid/(role+'.png')
   if target.exists():raw=target.read_bytes()
   else:
    h=client.read(e,e['offset'],30)
    if h[:4]!=b'PK\x03\x04':raise ValueError('Local header')
    n,x=struct.unpack_from('<HH',h,26);local=client.read(e,e['offset']+30,n+x)
    if local[:n].decode()!=e['name']:raise ValueError('Exact filename')
    payload=client.read(e,e['offset']+30+n+x,e['compressed'])
    if e['method']==8:
     dec=zlib.decompressobj(-15);raw=dec.decompress(payload,e['size']+1)
     if not dec.eof or dec.unconsumed_tail or dec.unused_data:raise ValueError('Deflate bounds')
    else:raw=payload
   if len(raw)!=e['size'] or zlib.crc32(raw)!=e['crc32']:raise ValueError('Indexed member identity')
   with Image.open(io.BytesIO(raw)) as im:
    im.load();png_info(raw,require_transparency=False,raster=im);w,h=im.size
   e['sha256']=sha(raw)
   if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
   result['artwork'].append({'banner_id':uid,'role':role,'provenance':'global-targeted-preservation-en-static-banner','sha256_basis':'Observed after pinned ZIP index / exact filename / CRC / PNG validation; not publisher attestation','entry':e,'index_path':str(ip.relative_to(IOS)),'index_sha256':sha(ip.read_bytes()),'cache_path':str(target.relative_to(IOS)),'width':w,'height':h})
 LOCK.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'images':len(result['artwork']),'ids':len({r['banner_id'] for r in result['artwork']}),'network_bytes':client.transferred}))
if __name__=='__main__':run()

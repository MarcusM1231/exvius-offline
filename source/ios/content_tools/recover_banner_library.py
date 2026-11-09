"""Bounded adjacent-member reads, resumable per-group checkpoints; no full archive fallback."""
import json,struct,zlib,time,io
from pathlib import Path
from import_content import IOS,sha
from banner_artwork_audit import ROOT,inventory
from range_client import RangeClient,RangeError
from png_validation import png_info
LOCK=Path(__file__).with_name('banner-library.lock.json')
def decode_member(data,start,e):
 at=e['offset']-start
 if at<0 or data[at:at+4]!=b'PK\x03\x04':raise ValueError('ZIP local header identity')
 method=struct.unpack_from('<H',data,at+8)[0];flags=struct.unpack_from('<H',data,at+6)[0]
 if method!=e['method'] or flags&1:raise ValueError('ZIP method/encryption')
 n,x=struct.unpack_from('<HH',data,at+26);p=at+30+n+x;end=p+e['compressed']
 if end>len(data) or data[at+30:at+30+n].decode()!=e['name']:raise ValueError('ZIP member bounds/name')
 payload=data[p:end]
 if method==8:
  dec=zlib.decompressobj(-15);raw=dec.decompress(payload,e['size']+1)
  if not dec.eof or dec.unconsumed_tail or dec.unused_data:raise ValueError('Deflate bounds')
 elif method==0:raw=payload
 else:raise ValueError('Unsupported ZIP compression')
 if len(raw)!=e['size'] or zlib.crc32(raw)!=e['crc32']:raise ValueError('ZIP CRC/size')
 return raw

def validate(raw,e):
 from PIL import Image
 if len(raw)!=e['size'] or zlib.crc32(raw)!=e['crc32']:raise ValueError('Image source identity')
 with Image.open(io.BytesIO(raw)) as im:
  im.load();png_info(raw,require_transparency=False,raster=im)
  if im.width<32 or im.height<16 or max(im.size)>4096:raise ValueError('Unexpected banner dimensions')
  return im.size

def recover():
 report=inventory();receipt=ROOT/'recovery.json';previous=json.loads(receipt.read_text()) if receipt.exists() else {'records':{},'batches':[]}
 cached={r['entry']['archive']+':'+r['entry']['name']:r for r in json.loads(Path(__file__).with_name('global-menu-art.lock.json').read_text())['artwork']}
 rows=[];pending=[];failures=[]
 def keep(c,path):
  raw=path.read_bytes();w,h=validate(raw,c['entry']);old=previous['records'].get(c['key'])
  digest=sha(raw)
  if old and old.get('sha256')!=digest:raise ValueError('Recovered cache changed')
  if c['key'] in cached and digest!=cached[c['key']]['entry']['sha256']:raise ValueError('Phase7B source changed')
  row=dict(c,status='successfully_recovered',cache_path=str(path.relative_to(IOS)),sha256=digest,width=w,height=h,language='English source namespace; visual/text validation tracked separately')
  previous['records'][c['key']]=row;rows.append(row)
 for c in report['candidates']:
  if not c['mapping']:
   previous['records'][c['key']]=c;continue
  e=c['entry'];path=IOS/cached[c['key']]['cache_path'] if c['key'] in cached else ROOT/'png-cache'/f"{e['archive']}-{e['offset']}.png"
  if path.exists():keep(c,path)
  elif e['size']>2_000_000 or e['compressed']>1_000_000:c['status']='found_but_unsupported_size';previous['records'][c['key']]=c
  else:pending.append((c,path))
 groups=[]
 for item in sorted(pending,key=lambda v:(v[0]['entry']['archive'],v[0]['entry']['offset'])):
  c,path=item;e=c['entry'];end=e['offset']+30+len(e['name'].encode())+e['compressed']+256
  if groups:
   g=groups[-1];last=g[-1][0]['entry'];lastend=last['offset']+30+len(last['name'].encode())+last['compressed']
   if last['archive']==e['archive'] and e['offset']-lastend<=256 and end-g[0][0]['entry']['offset']<=1_000_000 and len(g)<32:g.append(item);continue
  groups.append([item])
 client=None;newbytes=0
 def checkpoint():receipt.write_text(json.dumps(previous,indent=2)+'\n')
 checkpoint()
 for i,g in enumerate(groups):
  first=g[0][0]['entry'];last=g[-1][0]['entry'];start=first['offset'];end=min(first['archive_size'],last['offset']+30+len(last['name'].encode())+last['compressed']+256);length=end-start
  if client is None or client.transferred+length>client.max_bytes:
   old=client;client=RangeClient(interval=1,max_bytes=4*1024**2,journal=ROOT/f'batch-{time.time_ns()}.json')
   if old:client.last_request=old.last_request;client.resolved=old.resolved
  try:
   data=client.read(first,start,length);newbytes+=len(data)
   for c,path in g:
    raw=decode_member(data,start,c['entry']);validate(raw,c['entry']);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise ValueError('Refusing cache overwrite')
    path.write_bytes(raw);keep(c,path)
  except (RangeError,ValueError) as error:
   failures.append({'group':i,'reason':str(error),'remaining_groups':len(groups)-i});previous['last_failure']=failures[-1];checkpoint();break
  previous['batches'].append({'group_files':len(g),'range_bytes':len(data),'recovered_total':sum(r['status']=='successfully_recovered' for r in previous['records'].values())});checkpoint()
  print(json.dumps(previous['batches'][-1]),flush=True)
 result={'schema':1,'scope':report['scope'],'index_pins':report['index_pins'],'records':list(previous['records'].values()),'failures':failures,'network_bytes_this_run':newbytes}
 # Include every pending entry explicitly even if the server stopped part way.
 seen={r['key'] for r in result['records']}
 result['records'].extend(c for c in report['candidates'] if c['key'] not in seen)
 (ROOT/'classification.json').write_text(json.dumps(result,indent=2)+'\n')
 pins={'schema':1,'provenance_warning':'Global-targeted preservation and English source namespace are not retail CDN attestation; community calendar images remain separately labeled. No Memorial substitution.','artwork':[r for r in result['records'] if r['status']=='successfully_recovered'],'classification_counts':{s:sum(r['status']==s for r in result['records']) for s in sorted({r['status'] for r in result['records']})}}
 body=json.dumps(pins,indent=2)+'\n'
 if LOCK.exists() and LOCK.read_text()!=body:raise ValueError('Existing library lock differs; review classification before replacing it')
 if not LOCK.exists():LOCK.write_text(body)
 print(json.dumps({'counts':pins['classification_counts'],'new_network_bytes':newbytes,'failures':failures}),flush=True)
 return result
if __name__=='__main__':recover()

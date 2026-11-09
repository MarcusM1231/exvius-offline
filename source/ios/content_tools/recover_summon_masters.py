"""Selected original metadata only; pinned ZIP identities, bounded reads and no save access."""
import json,struct,zlib
from pathlib import Path
from import_content import IOS,sha,validate_source
from range_client import RangeClient
ROOT=IOS/'.local/phase7c/masters';LOCK=Path(__file__).with_name('summon-masters.lock.json')
NAMES=['F_TICKET_MST.ndjson','F_IMPORTANT_ITEM_MST.ndjson','F_ITEM_MST.ndjson','F_LIMITBURST_MST.ndjson']
def recover():
 ROOT.mkdir(parents=True,exist_ok=True);ip=IOS/'.local/phase6a/source-indexes/data-001-index.json';idx=json.loads(ip.read_text());entries={e['name']:e for e in idx['entries']}
 rows=json.loads(LOCK.read_text())['sources'] if LOCK.exists() else []
 if not rows:
  for name in NAMES:
   e=dict(entries['static/mst_decoded/'+name],archive='data-001',url=idx['url'],archive_size=idx['archive_size'])
   rows.append({'entry':e,'cache_path':str((ROOT/name).relative_to(IOS)),'index_sha256':sha(ip.read_bytes())})
 client=RangeClient(interval=1,max_bytes=2*1024**2,journal=ROOT/'ranges.json')
 for r in rows:
  if sha(ip.read_bytes())!=r['index_sha256']:raise ValueError('Master ZIP index identity')
  e=r['entry'];path=IOS/r['cache_path']
  if not path.exists():
   if e['compressed']>1024**2 or e['size']>8*1024**2:raise ValueError('Metadata bounds')
   h=client.read(e,e['offset'],30)
   if h[:4]!=b'PK\x03\x04':raise ValueError('ZIP header')
   n,x=struct.unpack_from('<HH',h,26);raw=client.read(e,e['offset']+30,n+x+e['compressed'])
   if raw[:n].decode()!=e['name']:raise ValueError('Metadata filename')
   dec=zlib.decompressobj(-15);body=dec.decompress(raw[n+x:],e['size']+1) if e['method']==8 else raw[n+x:]
   if e['method']==8 and (not dec.eof or dec.unconsumed_tail or dec.unused_data):raise ValueError('Deflate bounds')
   if len(body)!=e['size'] or zlib.crc32(body)!=e['crc32']:raise ValueError('Metadata CRC')
   if e.get('sha256') and sha(body)!=e['sha256']:raise ValueError('Metadata pin changed')
   path.write_bytes(body)
  body=path.read_bytes();digest=sha(body)
  if e.get('sha256') and e['sha256']!=digest:raise ValueError('Existing source changed')
  e['sha256']=digest;validate_source(body,e)
  r['rows']=len([json.loads(line) for line in body.decode().splitlines() if line.strip()])
 result={'schema':1,'scope':'Global-targeted preservation decoded master tables; observed SHA pins after exact ZIP member/CRC verification','sources':rows};text=json.dumps(result,indent=2)+'\n'
 if LOCK.exists() and LOCK.read_text()!=text:raise ValueError('Locked metadata changed')
 if not LOCK.exists():LOCK.write_text(text)
 print(json.dumps({'tables':{Path(r['entry']['name']).name:r['rows'] for r in rows},'network_bytes':client.transferred}))
if __name__=='__main__':recover()

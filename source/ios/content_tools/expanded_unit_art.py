"""Phase 7D exact-form static supplement. Does not change animation or gameplay locks."""
import argparse,collections,io,json,shutil,tempfile
from pathlib import Path
from import_content import IOS,sha,validate_png,build_catalog,DEFAULT_SOURCE,load_lock
import expand_artwork
from expand_artwork import source_key
from range_client import RangeClient
from import_summon_ui import decode
ROOT=IOS/'.local/phase7d/unit-art';LOCK=Path(__file__).with_name('expanded-unit-art.lock.json')
def output():return ROOT/'versions'/sha(LOCK.read_bytes())[:16]/'ExpandedUnitArt'
def png(body):
 from PIL import Image
 info=validate_png(body)
 with Image.open(io.BytesIO(body)) as im:
  im.load();a=im.convert('RGBA').getchannel('A');box=a.getbbox()
  if not box or a.getextrema()[0]!=0:raise ValueError('Missing visible pixels/transparency')
  return {'dimensions':list(im.size),'visible_bounds':list(box),'transparent':True}
def inventory():
 ROOT.mkdir(parents=True,exist_ok=True)
 audit=json.loads((IOS/'.local/phase7c/catalog/eligibility.json').read_text());enabled=[r for r in audit['records'] if r['eligible']];frequency=collections.Counter(u for r in enabled for u in r['required_units']);units=build_catalog(DEFAULT_SOURCE)['units'];old={r['unit_id'] for r in load_lock()['artwork']}|set(json.loads(__import__('import_extra_unit_art').output().joinpath('catalog.json').read_text()))
 client=RangeClient(journal=ROOT/'index-ranges.json',max_bytes=8*1024**2);matches=collections.defaultdict(list);pins={}
 for source in json.loads(Path(__file__).with_name('unit_sources.lock.json').read_text())['sources']:
  key=source_key(source);cached=ROOT/'discovery'/(key+'.json');previous_cache=IOS/'.local/unit-content/discovery'/(key+'.json')
  if not cached.exists() and previous_cache.exists():
   if LOCK.exists() and sha(previous_cache.read_bytes())!=json.loads(LOCK.read_text())['source_pins'][key]['index_sha256']:raise ValueError('Existing cached index pin mismatch')
   cached.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(previous_cache,cached)
  previous=expand_artwork.CACHE
  try:
   expand_artwork.CACHE=ROOT
   index,record=expand_artwork.read_index(source,client)
  finally:expand_artwork.CACHE=previous
  key=source_key(source);record['index_path']=str((ROOT/'discovery'/(key+'.json')).relative_to(IOS));pins[key]=record
  for entry in index['entries']:
   name=Path(entry['name']).name
   if name.startswith('unit_ills_') and name.endswith('.png') and name[10:-4] in frequency:
    uid=name[10:-4];matches[uid].append({'unit_id':uid,'entry':entry,'source_key':key})
 # Existing animation locks are read only; they do not authorize another form.
 animation=json.loads(Path(__file__).with_name('unit-animation-expanded.lock.json').read_text());animated=set(animation['units']) if isinstance(animation['units'],dict) else {str(r['unit_id']) if isinstance(r,dict) else str(r) for r in animation['units']}
 rows=[]
 for uid in sorted(frequency,key=lambda u:(units[u]['rarity_code']!=4,-frequency[u],u)):
  row=units[uid];rows.append({'unit_id':uid,'name':row['name'],'base_rarity':row['base_rarity_code'],'rarity':row['rarity_code'],'max_rarity':row['max_awakening_rarity_code'],'banner_frequency':frequency[uid],'static_before':uid in old,'animation_available':uid in animated,'sources':matches[uid],'source_searched':True,'status':'already_imported' if uid in old else 'indexed_not_imported' if matches[uid] else 'not_found_in_all_pinned_unit_cpk_indexes'})
 report={'schema':1,'provenance':'Global-targeted preservation; exact master-ID members, not retail Global CDN attestation. No Memorial substitution.','source_pins':pins,'records':rows,'index_network_bytes':client.transferred};(ROOT/'inventory.json').write_text(json.dumps(report,indent=2)+'\n');return report

def recover(batch=25):
 import time
 report=inventory();rows=[r for r in report['records'] if not r['static_before'] and r['sources']];art=[];client=RangeClient(interval=1,max_bytes=8*1024**2,journal=ROOT/('ranges-'+str(time.time_ns())+'.json'));(ROOT/'sources').mkdir(exist_ok=True);(ROOT/'rejected').mkdir(exist_ok=True)
 for i,r in enumerate(rows):
  candidates=[]
  for member in r['sources']:
   e=member['entry'];s=report['source_pins'][member['source_key']]
   if Path(e['name']).name!='unit_ills_'+r['unit_id']+'.png' or not 0<e['unpacked']<=128*1024 or not 0<e['size']<=128*1024 or e['offset_in_cpk']+e['size']>s['cpk_size']:raise ValueError('Exact source identity/bounds')
   path=ROOT/'sources'/(sha((member['source_key']+':'+e['name']).encode())+('.member' if e['size']!=e['unpacked'] else '.png'))
   rejected=ROOT/'rejected'/(r['unit_id']+'.member')
   raw=path.read_bytes() if path.exists() else rejected.read_bytes() if rejected.exists() else client.read(s,s['zip_payload_start']+e['offset_in_cpk'],e['size'])
   try:
    body=decode(raw)
    if len(raw)!=e['size'] or len(body)!=e['unpacked']:raise ValueError('Unsupported stored encoding or decoded size')
    info=png(body)
   except ValueError as error:
    if not rejected.exists():rejected.write_bytes(raw)
    r['status']='found_but_unsupported_or_invalid';r['recovery_error']=str(error);r['stored_sha256']=sha(raw);continue
   if not path.exists():path.write_bytes(raw)
   candidates.append(dict(member,sha256=sha(body),stored_sha256=sha(raw),cache_path=str(path.relative_to(IOS)),**info))
  if not candidates:continue
  if len({x['sha256'] for x in candidates})!=1:r['status']='conflicting_exact_source_versions';continue
  selected=candidates[0];art.append(dict(selected,provenance='original static PNG member',aliases=candidates[1:]));r['status']='recovered';r['sha256']=selected['sha256']
  if (i+1)%batch==0:
   (ROOT/('batch-%03d.json'%((i+1)//batch))).write_text(json.dumps({'processed':i+1,'recovered':len(art),'network_bytes':client.transferred},indent=2)+'\n');print('VERIFIED_BATCH',i+1,len(art),client.transferred,flush=True)
 lock={'schema':1,'source_pins':report['source_pins'],'artwork':sorted(art,key=lambda x:x['unit_id']),'unresolved':[r for r in report['records'] if r['status'] not in ('recovered','already_imported')]};text=json.dumps(lock,indent=2)+'\n'
 if LOCK.exists() and LOCK.read_text()!=text:raise ValueError('Pinned expanded artwork changed; review required')
 if not LOCK.exists():LOCK.write_text(text)
 report['network_bytes']=client.transferred;report['recovered_count']=len(art);(ROOT/'coverage.json').write_text(json.dumps(report,indent=2)+'\n');import_bundle();print(json.dumps({'recovered':len(art),'network_bytes':client.transferred,'bundle':str(output())}),flush=True)

def verify(root=None):
 root=Path(root or output());lock=json.loads(LOCK.read_text());receipt=json.loads((root/'receipt.json').read_text())
 if receipt['lock_sha256']!=sha(LOCK.read_bytes()):raise ValueError('Expanded artwork lock')
 if {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}!={'receipt.json'}|set(receipt['files']):raise ValueError('Expanded artwork file set')
 for name,digest in receipt['files'].items():
  if sha((root/name).read_bytes())!=digest:raise ValueError('Expanded artwork checksum')
 return receipt

def import_bundle():
 lock=json.loads(LOCK.read_text());rows=lock['artwork'];ids=[r['unit_id'] for r in rows]
 if len(set(ids))!=len(ids):raise ValueError('Duplicate master ID')
 for key,s in lock['source_pins'].items():
  ip=IOS/s['index_path']
  if sha(ip.read_bytes())!=s['index_sha256']:raise ValueError('CPK source index checksum')
 dest=output();dest.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
  stage=Path(tmp)/'ExpandedUnitArt';(stage/'images').mkdir(parents=True);catalog={}
  for r in rows:
   s=lock['source_pins'][r['source_key']];idx=json.loads((IOS/s['index_path']).read_text())
   if r['entry'] not in idx['entries'] or Path(r['entry']['name']).name!='unit_ills_'+r['unit_id']+'.png':raise ValueError('Exact member mismatch')
   raw=(IOS/r['cache_path']).read_bytes()
   if sha(raw)!=r['stored_sha256']:raise ValueError('Stored source checksum')
   body=decode(raw)
   if len(body)!=r['entry']['unpacked']:raise ValueError('Decoded source bounds')
   if sha(body)!=r['sha256'] or png(body)['dimensions']!=r['dimensions']:raise ValueError('Static source PNG checksum')
   name='images/'+r['sha256']+'.png';target=stage/name
   if not target.exists():target.write_bytes(body)
   catalog[r['unit_id']]={'file':name,'sha256':r['sha256']}
  (stage/'catalog.json').write_text(json.dumps(catalog,sort_keys=True,indent=2)+'\n');receipt={'lock_sha256':sha(LOCK.read_bytes()),'files':{str(p.relative_to(stage)):sha(p.read_bytes()) for p in sorted(stage.rglob('*')) if p.is_file()}};(stage/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
  if dest.exists():
   verify(dest)
   if (dest/'receipt.json').read_bytes()!=(stage/'receipt.json').read_bytes():raise ValueError('Nonreproducible expanded art')
  else:shutil.copytree(stage,dest)
 verify();return dest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--recover',action='store_true');a=p.parse_args();recover() if a.recover else import_bundle()

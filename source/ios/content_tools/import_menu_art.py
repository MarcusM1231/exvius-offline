"""Bundle only selected verified banner PNGs; no metadata rules or runtime downloads."""
import json,shutil,tempfile
from pathlib import Path
from import_content import IOS,sha
LOCK=Path(__file__).with_name('global-menu-art.lock.json')
def output():return IOS/'.local/phase7b/versions'/sha(LOCK.read_bytes())[:16]/'BannerArt'
def verify(root=None):
 root=Path(root or output());receipt=json.loads((root/'receipt.json').read_text())
 if receipt['lock_sha256']!=sha(LOCK.read_bytes()):raise ValueError('Banner art lock mismatch')
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}-{'receipt.json'}
 if actual!=set(receipt['files']):raise ValueError('Banner art file set changed')
 for name,digest in receipt['files'].items():
  if sha((root/name).read_bytes())!=digest:raise ValueError('Banner art checksum mismatch')
 return receipt

def run():
 from PIL import Image
 from png_validation import png_info
 lock=json.loads(LOCK.read_text());dest=output();dest.parent.mkdir(parents=True,exist_ok=True)
 keys=[(r['banner_id'],r['role']) for r in lock['artwork']]
 if len(set(keys))!=len(keys):raise ValueError('Duplicate banner ID/role')
 with tempfile.TemporaryDirectory(dir=dest.parent) as temp:
  root=Path(temp)/'BannerArt';(root/'images').mkdir(parents=True);catalog={}
  for r in lock['artwork']:
   uid,role=r['banner_id'],r['role']
   if not uid.isascii() or not uid.isdecimal() or role not in ('banner','detail_banner'):raise ValueError('Invalid exact ID/role')
   raw=(IOS/r['cache_path']).read_bytes()
   if sha(raw)!=r['entry']['sha256']:raise ValueError('Banner source checksum')
   with Image.open(IOS/r['cache_path']) as im:
    im.load();png_info(raw,require_transparency=False,raster=im)
    if list(im.size)!=[r['width'],r['height']]:raise ValueError('Banner dimensions')
   name=f'images/{uid}-{role}.png';(root/name).write_bytes(raw)
   catalog.setdefault(uid,{})[role]={'file':name,'width':r['width'],'height':r['height'],'provenance':r['provenance']}
  (root/'catalog.json').write_text(json.dumps(catalog,sort_keys=True,indent=2)+'\n')
  receipt={'lock_sha256':sha(LOCK.read_bytes()),'files':{str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}}
  (root/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
  if dest.exists():
   verify(dest)
   if (dest/'receipt.json').read_bytes()!=(root/'receipt.json').read_bytes():raise ValueError('Nonreproducible banner art')
  else:shutil.copytree(root,dest)
 verify();print(json.dumps({'images':len(keys),'ids':len(catalog),'bytes':sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()),'root':str(dest)}))
if __name__=='__main__':run()

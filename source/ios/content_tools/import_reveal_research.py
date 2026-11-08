"""Offline static SpriteStudio v1 cell research; no timeline or campaign access."""
import hashlib
import io
import json
from pathlib import Path
import struct
from import_summon_ui import decode

IOS = Path(__file__).resolve().parents[1]
LOCK = Path(__file__).with_name('reveal-research.lock.json')
CACHE = IOS / '.local/phase6a'

def sha(b): return hashlib.sha256(b).hexdigest()
def output(): return IOS / '.local/phase6d1/versions' / sha(LOCK.read_bytes())[:16] / 'RevealResearch'

def cells(body, textures):
    """Static unrotated SS5 v1 cells; reject invalid pointers/duplicates/bounds."""
    if len(body) < 28 or body[:4] != b'SSPB' or struct.unpack_from('<I', body, 4)[0] != 1:
        raise ValueError('Unsupported SSBP v1 header')
    start, _, count, _ = struct.unpack_from('<IIHH', body, 16)
    if count > 4096 or start < 28 or start+count*20 > len(body): raise ValueError('Cell table bounds')
    def string(n):
        if not 0 < n < len(body): raise ValueError('String pointer bounds')
        end = body.find(b'\0', n, min(len(body),n+1024))
        if end < 0: raise ValueError('Unterminated cell string')
        return body[n:end].decode('utf-8')
    result = {}
    for i in range(count):
        n,m,_,x,y,w,h,_ = struct.unpack_from('<IIhhhHHh', body, start+i*20)
        if m < 28 or m+8 > len(body): raise ValueError('Cell-map bounds')
        _,img = struct.unpack_from('<II', body, m)
        name, image = string(n), string(img)
        if name in result: raise ValueError('Duplicate cell name')
        if image not in textures: raise ValueError('Missing atlas page: '+image)
        atlas=textures[image]
        if x<0 or y<0 or w<1 or h<1 or x+w>atlas.width or y+h>atlas.height: raise ValueError('Crop bounds')
        result[name]=(atlas.crop((x,y,x+w,y+h)),{'texture':image,'rect':[x,y,w,h]})
    return result

def run(destination=None, cache=CACHE, lock_path=None):
    from PIL import Image
    lock_path=Path(lock_path or LOCK)
    lock=json.loads(lock_path.read_text()); bodies=[]
    for row in lock['sources']:
        b=(Path(cache)/row['cache_path']).read_bytes()
        if sha(b)!=row['sha256_stored']:raise ValueError('Source checksum mismatch')
        b=decode(b)
        if sha(b)!=row['sha256_decoded']:raise ValueError('Decoded checksum mismatch')
        bodies.append(b)
    with Image.open(io.BytesIO(bodies[1])) as im:
        im.load();atlas=im.convert('RGBA')
    crop=cells(bodies[0],{'gacha_result_animation.png':atlas})
    root=Path(destination or output());root.mkdir(parents=True,exist_ok=True)
    catalog={'schema':1,'notice':lock['scope'],'provenance':lock['provenance'],'assets':[]}
    hashes={}
    for name in lock['cells']:
        im,metadata=crop[name];stream=io.BytesIO();im.save(stream,format='PNG');b=stream.getvalue();p=root/(name+'.png')
        if p.exists() and p.read_bytes()!=b:raise ValueError('Refusing to overwrite changed research image')
        if not p.exists():p.write_bytes(b)
        hashes[p.name]=sha(b)
        catalog['assets'].append(dict(id=name,file=p.name,width=im.width,height=im.height,**metadata))
    b=(json.dumps(catalog,sort_keys=True,indent=2)+'\n').encode();p=root/'catalog.json'
    if p.exists() and p.read_bytes()!=b:raise ValueError('Refusing to overwrite changed research catalog')
    if not p.exists():p.write_bytes(b)
    hashes[p.name]=sha(b)
    receipt={'lock_sha256':sha(lock_path.read_bytes()),'files':hashes}
    (root/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    verify(root,lock_path=lock_path)
    return receipt

def verify(root=None,lock_path=None):
    lock_path=Path(lock_path or LOCK)
    root=Path(root or output());receipt=json.loads((root/'receipt.json').read_text())
    if receipt['lock_sha256']!=sha(lock_path.read_bytes()):raise ValueError('Research lock checksum mismatch')
    expected={name+'.png' for name in json.loads(lock_path.read_text())['cells']}|{'catalog.json'}
    if set(receipt['files'])!=expected:raise ValueError('Research receipt file set mismatch')
    for name,digest in receipt['files'].items():
        if sha((root/name).read_bytes())!=digest:raise ValueError('Research output checksum mismatch')
    return receipt

if __name__=='__main__':print(json.dumps(run(),indent=2))

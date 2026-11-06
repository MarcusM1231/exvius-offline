"""Build-time, cache-only import of selected Global layouts and UI textures.

Pillow is required only to import; Xcode packaging verifies hashes with stdlib.
No backend, save, unit-content cache or network access is used.
"""
import hashlib
import io
import json
from pathlib import Path
import plistlib
import re
import shutil
import struct
import tempfile

IOS = Path(__file__).resolve().parents[1]
CACHE = IOS / '.local/phase6a'
LOCK = Path(__file__).with_name('summon-ui.lock.json')

def sha(body): return hashlib.sha256(body).hexdigest()
def output(): return IOS / '.local/summon-ui/versions' / sha(LOCK.read_bytes())[:16] / 'SummonUI'

def decode(body):
    if not body.startswith(b'CRILAYLA'): return body
    if len(body)<16: raise ValueError('Truncated CRILAYLA header')
    count, packed = struct.unpack_from('<II', body, 8)
    if count > 16*1024**2 or 16+packed+256 > len(body): raise ValueError('CRILAYLA bounds')
    pos, bits, value = 16+packed-1, 0, 0
    def read(n):
        nonlocal pos, bits, value
        result = 0
        for _ in range(n):
            if not bits:
                if pos < 16: raise ValueError('Truncated CRILAYLA')
                value=body[pos];pos-=1;bits=8
            bits-=1;result=(result<<1)|((value>>bits)&1)
        return result
    result=bytearray()
    while len(result)<count:
        if not read(1): result.append(read(8));continue
        distance,length=read(13)+3,3
        for width in (2,3,5):
            n=read(width);length+=n
            if n != (1<<width)-1:break
        else:
            while True:
                n=read(8);length+=n
                if n!=255:break
        if distance>len(result) or len(result)+length>count:raise ValueError('CRILAYLA reference bounds')
        for _ in range(length):result.append(result[-distance])
    return body[16+packed:16+packed+256]+bytes(reversed(result))

def source(row, cache=CACHE):
    p=Path(cache)/row['cache_path'];body=p.read_bytes()
    if sha(body)!=row['sha256']:raise ValueError('Source checksum mismatch: '+row['cache_path'])
    if 'member' in row:
        from cpk_reader import index
        entries=index(p)['entries'];entry=next(e for e in entries if e['name']==row['member'])
        body=body[entry['offset']:entry['offset']+entry['size']]
        if sha(body)!=row['member_sha256']:raise ValueError('CPK member checksum mismatch')
    return decode(body)

def numbers(value,n):
    values=[int(x) for x in re.findall(r'-?\d+',value)]
    if len(values)!=n:raise ValueError('Invalid atlas geometry')
    return values

def frame_image(atlas, frame):
    """Restore an upright source canvas; support legacy and format-3 key names."""
    from PIL import Image
    x,y,w,h=numbers(frame.get('frame',frame.get('textureRect','')),4)
    rotated=frame.get('rotated',frame.get('textureRotated',False))
    sw,sh=numbers(frame.get('sourceSize',frame.get('spriteSourceSize','')),2)
    rect=frame.get('sourceColorRect')
    if rect: dx,dy,tw,th=numbers(rect,4)
    else:
        tw,th=numbers(frame['spriteSize'],2)
        ox,oy=numbers(frame.get('offset',frame.get('spriteOffset','{0,0}')),2)
        dx,dy=(sw-tw)//2+ox,(sh-th)//2-oy
    # TexturePacker records unrotated frame size in legacy frame, physical rect in textureRect.
    pw,ph=(h,w) if rotated and 'frame' in frame else (w,h)
    if min(pw,ph,sw,sh,tw,th)<=0 or max(sw,sh)>4096 or x<0 or y<0 or x+pw>atlas.width or y+ph>atlas.height:
        raise ValueError('Atlas bounds')
    image=atlas.crop((x,y,x+pw,y+ph))
    if rotated:image=image.transpose(Image.Transpose.ROTATE_90)
    if image.size!=(tw,th) or dx<0 or dy<0 or dx+tw>sw or dy+th>sh:raise ValueError('Atlas trim mismatch')
    canvas=Image.new('RGBA',(sw,sh));canvas.paste(image,(dx,dy));return canvas

def verify(root=None):
    root=Path(root or output());receipt=json.loads((root/'receipt.json').read_text())
    if receipt['lock_sha256']!=sha(LOCK.read_bytes()):raise ValueError('Summon UI lock mismatch')
    for name,digest in receipt['files'].items():
        if sha((root/name).read_bytes())!=digest:raise ValueError('Summon UI checksum mismatch: '+name)
    return receipt

def run(destination=None, cache=CACHE):
    from PIL import Image
    lock=json.loads(LOCK.read_text());dest=Path(destination or output())
    if len({r['id'] for r in lock['assets']})!=len(lock['assets']):raise ValueError('Duplicate UI asset ID')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        stage=Path(tmp)/'SummonUI';(stage/'images').mkdir(parents=True)
        blobs={k:source(r,cache) for k,r in lock['sources'].items()}
        layouts={}
        for key,source_id in lock['layouts'].items():
            rows={}
            for line in blobs[source_id].decode('utf-8-sig').splitlines():
                fields=line.split(',')
                if len(fields)<7:raise ValueError('Invalid layout CSV')
                if fields[5] in rows:raise ValueError('Duplicate layout anchor')
                rows[fields[5]]={'x':int(fields[0]),'y':int(fields[1]),'width':int(fields[2]),'height':int(fields[3]),'texture':fields[6]}
            layouts[key]=rows
        assets={}
        for row in lock['assets']:
            raw=blobs[row['source']]
            if 'frame' in row:
                frames=plistlib.loads(blobs[row['plist']])['frames']
                image=frame_image(Image.open(io.BytesIO(raw)).convert('RGBA'),frames[row['frame']])
            else:
                image=Image.open(io.BytesIO(raw));image.load();image=image.convert('RGBA')
            name='images/'+row['id']+'.png';image.save(stage/name,optimize=False,compress_level=9)
            assets[row['id']]={'file':name,'width':image.width,'height':image.height,'source':row['source'],'frame':row.get('frame')}
        catalog={'schema':1,'target':'Global 9.1.0 layouts + verified preservation textures','layouts':layouts,'assets':assets,'fallbacks':lock['fallbacks']}
        (stage/'catalog.json').write_text(json.dumps(catalog,sort_keys=True,indent=2)+'\n')
        files={str(p.relative_to(stage)):sha(p.read_bytes()) for p in stage.rglob('*') if p.is_file()}
        receipt={'lock_sha256':sha(LOCK.read_bytes()),'files':files,'source_sha256s':{k:sha(v) for k,v in blobs.items()}}
        (stage/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
        if dest.exists():
            verify(dest)
            if json.loads((dest/'receipt.json').read_text())!=receipt:raise ValueError('Non-reproducible output; refusing overwrite')
        else:stage.rename(dest)
    return verify(dest)

if __name__=='__main__':
    print(json.dumps(run(),indent=2));print(output())

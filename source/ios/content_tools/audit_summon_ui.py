"""Inspect cached Global/Memorial layouts and atlases; no originals changed."""
from pathlib import Path
import json,hashlib,plistlib,io,csv
from import_content import IOS
from import_summon_ui import decode,frame_image
ROOT=IOS/'.local/phase6a'
def sha(b):return hashlib.sha256(b).hexdigest()
def inspect():
    global_root=ROOT/'global/extracted/layout/gacha';memorial_root=ROOT/'memorial/extracted/layout/gacha'
    layouts=[]
    for p in sorted(global_root.glob('*.csv')):
        body=decode(p.read_bytes());other=memorial_root/p.name;rows=list(csv.reader(body.decode('utf-8-sig').splitlines()))
        layouts.append({'name':p.name,'global_cache':str(p.relative_to(IOS)),'global_decoded_sha256':sha(body),'memorial_cache':str(other.relative_to(IOS)) if other.exists() else None,'decoded_identical':other.exists() and decode(other.read_bytes())==body,'rows':rows})
    from PIL import Image
    atlas_sets={};atlases=[]
    for origin,base in [('global-targeted-preservation',ROOT/'preservation/extracted/Ver162_resources_tutorial/image/ui/gacha'),('memorial-english-patched',ROOT/'memorial/extracted/image/ui/gacha')]:
        atlas_sets[origin]={}
        for family in ['gacha','gacha2','gacha3']:
            plist=base/(family+'.plist');png=base/(family+'.png')
            if not plist.exists() or not png.exists():continue
            raw=decode(plist.read_bytes());pixels=decode(png.read_bytes());meta=plistlib.loads(raw)
            with Image.open(io.BytesIO(pixels)) as image:
                image.load();image=image.convert('RGBA');normalized={}
                for name,frame in meta['frames'].items():
                    im=frame_image(image,frame);normalized[name]={'size':list(im.size),'rgba_sha256':sha(im.tobytes())}
            atlas_sets[origin][family]=normalized;atlases.append({'origin':origin,'family':family,'plist_cache':str(plist.relative_to(IOS)),'png_cache':str(png.relative_to(IOS)),'plist_decoded_sha256':sha(raw),'png_decoded_sha256':sha(pixels),'frames':len(normalized),'frame_names':sorted(normalized)})
    comparisons=[]
    for family in ['gacha','gacha2','gacha3']:
        a=atlas_sets['global-targeted-preservation'].get(family,{});b=atlas_sets['memorial-english-patched'].get(family,{});shared=set(a)&set(b)
        comparisons.append({'family':family,'shared_frame_names':len(shared),'identical_source_canvas_rgba':[k for k in sorted(shared) if a[k]==b[k]],'different_frames':[k for k in sorted(shared) if a[k]!=b[k]],'global_target_only':sorted(set(a)-set(b)),'memorial_only':sorted(set(b)-set(a))})
    return {'schema':1,'global_client':'Original Global 9.1.0 cached resources; identity pinned by phase6a-asset-inventory.json','memorial_client':'English-patched Memorial 11.1.0; separate provenance','layouts':layouts,'memorial_only_layouts':sorted(p.name for p in memorial_root.glob('*.csv') if not (global_root/p.name).exists()),'atlases':atlases,'comparisons':comparisons,'interpretation':'Matching layout or normalized frame bytes does not prove scene behavior or unit-ID equivalence. No Memorial resource is substituted into production.'}
if __name__=='__main__':
    out=IOS/'.local/phase7a/ui-comparison.json';out.parent.mkdir(exist_ok=True);r=inspect();out.write_text(json.dumps(r,indent=2));print(json.dumps({'layouts':len(r['layouts']),'identical_layouts':sum(r['decoded_identical'] for r in r['layouts']),'atlas_comparisons':[{k:v for k,v in r.items() if k not in ['different_frames','global_target_only','memorial_only']} for r in r['comparisons']]}))

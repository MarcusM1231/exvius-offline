"""Reproducible build-time part assembly. Runtime receives bounded exact-ID frames."""
import json, shutil, tempfile
from pathlib import Path
from import_content import IOS,sha
from import_summon_ui import decode
from png_validation import png_info
LEGACY_LOCK=Path(__file__).with_name('unit-animation-sources.lock.json')
EXPANDED_LOCK=Path(__file__).with_name('unit-animation-expanded.lock.json')
LOCK=EXPANDED_LOCK if EXPANDED_LOCK.exists() else LEGACY_LOCK
CACHE=IOS/'.local/phase6d4/sources'
def output():return IOS/'.local/unit-animations/versions'/sha(LOCK.read_bytes())[:16]/'UnitAnimations'
def checked(name,lock):
    row=next(r for r in lock['members'] if r['name']==name);raw=(IOS/row['cache_path'] if 'cache_path' in row else CACHE/name).read_bytes()
    if len(raw)!=row['size'] or sha(raw)!=row['sha256_stored']:raise ValueError('Animation stored checksum')
    body=decode(raw)
    if len(body)!=row['unpacked'] or sha(body)!=row['sha256_decoded']:raise ValueError('Animation decoded checksum')
    return body

def build(lock_path=None, destination=None, kinds=None, research_root=None, report_path=None, dynamic_attacks=False):
    from PIL import Image,ImageDraw
    from unit_animation import parse_cgg,parse_cgs,compose,staging_bounds
    active_lock=Path(lock_path or LOCK)
    action_kinds=tuple(kinds or ('idle','standby'))
    if any(k not in ('idle','standby','atk','magic_atk','win_before','win') for k in action_kinds):raise ValueError('Unreviewed action type')
    lock=json.loads(active_lock.read_text());dest=Path(destination or output());dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent) as temp:
        root=Path(temp)/'UnitAnimations';root.mkdir();reports={};catalog={}
        for uid in sorted({r['name'].split('_')[-1].split('.')[0] for r in lock['members']}):
            texbody=checked(f'unit_anime_{uid}.png',lock)
            import io
            with Image.open(io.BytesIO(texbody)) as original:
                if original.width>4096 or original.height>4096:raise ValueError("Animation sheet dimension budget")
                original.load();png_info(texbody,raster=original,maximum_dimension=4096)
                texture=original.convert('RGBA')
            # Parse only the selected composition rows. Other actions can carry
            # unsupported transforms and remain explicitly unimplemented.
            cggtext=checked(f'unit_cgg_{uid}.csv',lock).decode('utf-8');lines=cggtext.splitlines()
            reports[uid]={'total_composition_rows':len(lines),'animations':{},'unsupported':{}};catalog[uid]={}
            for kind in action_kinds:
                if not any(r['name']==f'unit_{kind}_cgs_{uid}.csv' for r in lock['members']):continue
                try:
                    seq=parse_cgs(checked(f'unit_{kind}_cgs_{uid}.csv',lock).decode(),len(lines))
                    if len(seq)>64:raise ValueError('Runtime sequence exceeds 64-frame budget')
                    selected={r['composition']:parse_cgg(lines[r['composition']],texture.size)[0] for r in seq}
                    dynamic=dynamic_attacks and kind=='atk'
                    stage=staging_bounds(selected,seq) if dynamic else (0,0,512,512)
                    origin=(-stage[0],-stage[1]) if dynamic else (256,384)
                    canvas=(stage[2]-stage[0],stage[3]-stage[1])
                    frames=[compose(texture,selected[r['composition']],(r['offset_x'],r['offset_y']),canvas=canvas,origin=origin) for r in seq]
                    boxes=[f.getbbox() for f in frames]
                    if any(b is None for b in boxes):raise ValueError('Empty frame')
                    box=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
                    frames=[f.crop(box) for f in frames]
                    if len(frames)>64 or frames[0].width*frames[0].height*len(frames)*4>(33554432 if dynamic else 8388608):raise ValueError('Runtime pixel/frame budget')
                    paths=[]
                    for n,im in enumerate(frames):
                        name=f'{uid}/{kind}/{n}.png';p=root/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p);paths.append(name)
                    meta={'masterID':uid,'kind':kind,'ticks':[r['ticks'] for r in seq],'frames':paths,'width':frames[0].width,'height':frames[0].height,'timebase':60,'timebase_status':'community convention; retail client unverified','anchor':[origin[0]-box[0],origin[1]-box[1]]}
                    catalog[uid][kind]=meta
                    reports[uid]['animations'][kind]={'sequence':seq,'parts':{str(k):v for k,v in selected.items()},'bounds':box,'source_staging_bounds':stage,'unique_pixel_frames':len({f.tobytes() for f in frames})}
                    if (lock_path is not None and not dynamic_attacks) or uid in ['100004604','100005404','205000703','202000203','100000103','206000103','206000113','100008605','100009903','100011004'] or uid in sorted(catalog)[:25]:
                        research=Path(research_root) if research_root else IOS/'.local/phase6d4/previews';research.mkdir(parents=True,exist_ok=True)
                        contact=Image.new('RGB',(len(frames)*160,200),(30,35,52));draw=ImageDraw.Draw(contact)
                        for n,im in enumerate(frames):
                            enlarged=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);enlarged.thumbnail((150,170),Image.Resampling.NEAREST);contact.paste(enlarged,(n*160+(160-enlarged.width)//2,25),enlarged);draw.text((n*160+8,8),f'{n}: CGG {seq[n]["composition"]}',fill='white')
                        contact.save(research/f'{uid}-{kind}-contact.png')
                        frames[0].save(research/f'{uid}-{kind}.gif',save_all=True,append_images=frames[1:],duration=[round(r['ticks']/60*1000) for r in seq],loop=0,disposal=2)
                except ValueError as error:reports[uid]['unsupported'][kind]=str(error)
        coverage={}
        if active_lock==EXPANDED_LOCK or dynamic_attacks:
            from expand_unit_animations import plan
            _,_,inventory=plan()
            for uid,u in inventory.items():
                supported=list(catalog.get(uid,{}))
                reason=reports.get(uid,{}).get('unsupported',{}).get('idle','Not recovered or missing exact-ID resources') if 'idle' not in supported else ''
                metadata=catalog.get(uid,{})
                image_paths={p for m in metadata.values() for p in m['frames']}
                coverage[uid]={**u,'supported':supported,'reason':reason,**({'unsupported':reports.get(uid,{}).get('unsupported',{})} if dynamic_attacks else {}),'status':'supported idle' if 'idle' in supported else 'static fallback',
                    'estimated_bundle_bytes':sum((root/p).stat().st_size for p in image_paths)+len(json.dumps(metadata).encode()),
                    'decoded_clip_bytes':{k:m['width']*m['height']*len(m['frames'])*4 for k,m in metadata.items()}}
        if lock_path is not None:
            (root/'support.json').write_text(json.dumps({uid:{'available':list(catalog[uid]),'unsupported':r['unsupported']} for uid,r in reports.items()},sort_keys=True))
        (root/'coverage.json').write_text(json.dumps(coverage,sort_keys=True))
        (root/'catalog.json').write_text(json.dumps(catalog,sort_keys=True,separators=(',',':')))
        files={str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
        (root/'receipt.json').write_text(json.dumps({'lock_sha256':sha(active_lock.read_bytes()),'files':files},sort_keys=True,indent=2)+'\n')
        (Path(report_path) if report_path else IOS/('.local/phase6d4b/format-report.json' if active_lock==EXPANDED_LOCK else '.local/phase6d4/format-report.json')).write_text(json.dumps(reports,indent=2)+'\n')
        if dest.exists():
            if any(not (dest/name).exists() or sha((dest/name).read_bytes())!=digest for name,digest in files.items()):raise ValueError('Existing output differs')
        else:shutil.copytree(root,dest)
    verify(root=dest,lock_path=active_lock);return {k:list(v) for k,v in catalog.items()}
def verify(root=None,lock_path=None):
    root=Path(root or output());active_lock=Path(lock_path or LOCK);r=json.loads((root/'receipt.json').read_text())
    if r['lock_sha256']!=sha(active_lock.read_bytes()):raise ValueError('Animation lock identity')
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}-{'receipt.json'}
    if actual!=set(r['files']):raise ValueError('Animation file set')
    for name,digest in r['files'].items():
        if sha((root/name).read_bytes())!=digest:raise ValueError('Animation output checksum')
if __name__=='__main__':print(json.dumps(build(),indent=2))

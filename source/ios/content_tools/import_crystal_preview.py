"""Cache-only import for the isolated original-mesh diagnostic (not BMB playback)."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from import_summon_ui import decode
from crystal_formats import ibmb_info, m3r_mesh

IOS=Path(__file__).resolve().parents[1]
LOCK=Path(__file__).with_name('crystal-preview.lock.json')
def sha(body):return hashlib.sha256(body).hexdigest()
def output():return IOS/'.local/crystal-preview/versions'/sha(LOCK.read_bytes())[:16]/'CrystalPreview'
def read_source(row):
    body=(IOS/'.local'/row['cache_path']).read_bytes()
    if len(body)!=row['stored_size'] or sha(body)!=row['stored_sha256']:raise ValueError('Crystal source checksum mismatch')
    decoded=decode(body)
    if len(decoded)!=row['decoded_size'] or sha(decoded)!=row['decoded_sha256']:raise ValueError('Decoded crystal checksum mismatch')
    return decoded

def verify(root=None):
    root=Path(root or output());r=json.loads((root/'receipt.json').read_text())
    if r['lock_sha256']!=sha(LOCK.read_bytes()):raise ValueError('Crystal lock mismatch')
    if set(r['files'])!={'mesh.json','texture.png','catalog.json'}:raise ValueError('Unexpected crystal files')
    for name,digest in r['files'].items():
        if sha((root/name).read_bytes())!=digest:raise ValueError('Crystal bundle checksum mismatch')
    return r

def run(destination=None):
    from PIL import Image
    import io
    lock=json.loads(LOCK.read_text());decoded={key:read_source(row) for key,row in lock['sources'].items()}
    # Probe every selected BMB/model but package only the one inspected crystal.
    findings={}
    for key,body in decoded.items():
        if body[:4]==b'IBMB':findings[key]=ibmb_info(body)
        elif body[:4]==b'BR3M':
            info=m3r_mesh(body);findings[key]={k:v for k,v in info.items() if k not in ['positions','normals','uvs','vertex_colors_raw','indices']}
    mesh=m3r_mesh(decoded['mother-001'])
    if mesh['texture_names']!=['deff_mothercrystal_001']:raise ValueError('Unresolved model texture')
    with Image.open(io.BytesIO(decoded['mother-texture'])) as image:image.load();width,height=image.size
    target=Path(destination or output());target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        stage=Path(tmp)/'CrystalPreview';stage.mkdir()
        (stage/'mesh.json').write_text(json.dumps(mesh,sort_keys=True,separators=(',',':'))+'\n')
        (stage/'texture.png').write_bytes(decoded['mother-texture'])
        catalog={'schema':1,'label':'Original mother-crystal mesh diagnostic','original_animation_recovered':False,
                 'source':'Global-targeted preservation; not proof of original retail CDN byte provenance',
                 'appearance':'Original geometry, UVs and texture. Diagnostic camera and lighting; BISHAMON material/timeline not implemented.',
                 'texture_size':[width,height],'vertices':mesh['vertices'],'triangles':mesh['triangles'],
                 'gpu_payload_lower_bound_bytes':mesh['vertices']*48+len(mesh['indices'])*4+width*height*4,
                 'findings':findings,'blockers':['BMB node/curve interpretation','material and texture override binding','particle emission/random seeds','camera and original timing','gacha input/upgrade/skip sequence']}
        (stage/'catalog.json').write_text(json.dumps(catalog,sort_keys=True,indent=2)+'\n')
        receipt={'lock_sha256':sha(LOCK.read_bytes()),'files':{p.name:sha(p.read_bytes()) for p in stage.iterdir()},'sources':lock['sources']}
        (stage/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
        if target.exists():
            if verify(target)!=receipt:raise ValueError('Refusing non-reproducible crystal bundle')
        else:stage.rename(target)
    return verify(target)

if __name__=='__main__':
    print(json.dumps(run(),indent=2));print(output())

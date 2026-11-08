"""Cache-only original assets for a separately labelled reconstructed preview."""
import json
from pathlib import Path
import tempfile
from import_crystal_preview import read_source, sha
from crystal_formats import m3r_mesh
from png_validation import png_info

IOS=Path(__file__).resolve().parents[1]
LOCK=Path(__file__).with_name('crystal-reconstruction.lock.json')
FILES={*(f'model{i:03}.json' for i in range(1,6)),*(k+'.png' for k in ['texture001','texture002','texture004','prismatic','glow','halo','burst']),'catalog.json'}

def output():return IOS/'.local/crystal-reconstruction/versions'/sha(LOCK.read_bytes())[:16]/'CrystalReconstruction'

def verify(root=None):
    root=Path(root or output());receipt=json.loads((root/'receipt.json').read_text())
    if receipt['lock_sha256']!=sha(LOCK.read_bytes()) or set(receipt['files'])!=FILES:raise ValueError('Reconstruction receipt mismatch')
    for name,digest in receipt['files'].items():
        if sha((root/name).read_bytes())!=digest:raise ValueError('Reconstruction bundle checksum')
    return receipt

def run(destination=None):
    lock=json.loads(LOCK.read_text());blobs={k:read_source(r) for k,r in lock['sources'].items()};target=Path(destination or output());target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        stage=Path(temp)/'CrystalReconstruction';stage.mkdir();models={};textures={}
        for key,body in blobs.items():
            if key.startswith('model'):
                mesh=m3r_mesh(body);models[key]={k:mesh[k] for k in ['vertices','triangles','bounds','texture_names','sections','material_words']}
                (stage/(key+'.json')).write_text(json.dumps(mesh,sort_keys=True,separators=(',',':'))+'\n')
            else:
                textures[key]=png_info(body,require_transparency=False)
                (stage/(key+'.png')).write_bytes(body)
        catalog={'schema':1,'scope':lock['scope'],'models':models,'textures':textures,'original_animation_recovered':False,
                 'provenance':'Global-targeted preservation, not retail CDN byte provenance; no third-party runtime/content imported',
                 'uv_policy':'Original M3R UV and triangle indices unchanged. No Effekseer V/winding conversion.',
                 'layer_roles':'Reconstructed choices, not recovered BISHAMON bindings. Model003 is an optional partial shell, never original shards.'}
        (stage/'catalog.json').write_text(json.dumps(catalog,sort_keys=True,indent=2)+'\n')
        receipt={'schema':1,'lock_sha256':sha(LOCK.read_bytes()),'files':{p.name:sha(p.read_bytes()) for p in stage.iterdir()},'sources':lock['sources']}
        (stage/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
        if target.exists():
            if verify(target)!=receipt:raise ValueError('Refusing differing reconstruction output')
        else:stage.rename(target)
    return verify(target)

if __name__=='__main__':
    run();print(output())

"""Cache-only optional original English prompt and cloud texture; no saves/network."""
import json
from pathlib import Path
from import_content import IOS,sha
from png_validation import png_info
LOCK=Path(__file__).with_name('crystal-entrance.lock.json')
CACHE=IOS/'.local'
def output():return IOS/'.local/crystal-entrance/versions'/sha(LOCK.read_bytes())[:16]/'CrystalEntrance'
def run(destination=None,cache=CACHE):
    lock=json.loads(LOCK.read_text());root=Path(destination or output());root.mkdir(parents=True,exist_ok=True);files={}
    for row in lock['members']:
        body=(Path(cache)/row['cache_path']).read_bytes()
        if sha(body)!=row['sha256']:raise ValueError('Entrance source checksum')
        png_info(body)
        name=row['id']+'.png';p=root/name
        if p.exists() and p.read_bytes()!=body:raise ValueError('Refusing to overwrite changed entrance artwork')
        if not p.exists():p.write_bytes(body)
        files[name]=sha(body)
    receipt={'lock_sha256':sha(LOCK.read_bytes()),'files':files,'notice':lock['scope']}
    (root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');verify(root);return receipt
def verify(root=None):
    root=Path(root or output());r=json.loads((root/'receipt.json').read_text());lock=json.loads(LOCK.read_text())
    if r['lock_sha256']!=sha(LOCK.read_bytes()) or r['files']!={x['id']+'.png':x['sha256'] for x in lock['members']}:raise ValueError('Entrance receipt checksum')
    for name,h in r['files'].items():
        if sha((root/name).read_bytes())!=h:raise ValueError('Entrance output checksum')
    return r
if __name__=='__main__':print(json.dumps(run(),indent=2))

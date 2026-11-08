"""Production attack bundle; reuse the one CGG/CGS importer, preserve old idle bytes."""
import json
from pathlib import Path
from import_content import IOS,sha
from import_unit_animations import build as assemble,verify as check
LOCK=Path(__file__).with_name('unit-attack-expanded.lock.json')
ROOT=IOS/'.local/phase6d4d'
def output():return ROOT/'versions'/sha(LOCK.read_bytes())[:16]/'UnitAnimations'
def build():
    return assemble(lock_path=LOCK,destination=output(),kinds=['idle','standby','atk'],research_root=ROOT/'previews',report_path=ROOT/'format-report.json',dynamic_attacks=True)
def verify():check(root=output(),lock_path=LOCK)
if __name__=='__main__':
    c=build();print(json.dumps({'units':len(c),'attacks':sum('atk' in k for k in c.values()),'output':str(output())}))

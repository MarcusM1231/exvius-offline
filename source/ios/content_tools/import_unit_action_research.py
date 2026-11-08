"""Use the existing assembler for an isolated Developer-only action bundle."""
import json
from pathlib import Path
from import_content import IOS,sha
import import_unit_animations as importer
LOCK=Path(__file__).with_name('unit-action-research.lock.json')
ROOT=IOS/'.local/phase6d4c'
def output():return ROOT/'versions'/sha(LOCK.read_bytes())[:16]/'UnitActionResearch'
def run():
    return importer.build(lock_path=LOCK,destination=output(),kinds=('idle','standby','atk','magic_atk','win_before','win'),research_root=ROOT/'previews',report_path=ROOT/'action-format-report.json')
def verify():return importer.verify(root=output(),lock_path=LOCK)
if __name__=='__main__':print(json.dumps(run(),indent=2))

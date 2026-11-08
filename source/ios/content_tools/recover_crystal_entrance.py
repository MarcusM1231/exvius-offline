"""One pinned common TOUCH SCREEN member; reuse existing bounded recovery checks."""
from pathlib import Path
import json
from import_content import IOS
import recover_crystal_reconstruction as recovery
LOCK=Path(__file__).with_name('crystal-entrance-source.lock.json')
CACHE=IOS/'.local/phase6d3a'
def run(client=None):return recovery.run(client,lock_path=LOCK,cache=CACHE)
if __name__=='__main__':print(json.dumps(run(),indent=2))

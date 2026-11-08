"""Pinned production reveal cells; reuse the bounded static research crop decoder."""
import json
from pathlib import Path
import import_reveal_research as research
from import_content import IOS,sha
LOCK=Path(__file__).with_name('character-reveal.lock.json')
def output():return IOS/'.local/character-reveal/versions'/sha(LOCK.read_bytes())[:16]/'CharacterReveal'
def run(destination=None,cache=research.CACHE):
    return research.run(destination or output(),cache=cache,lock_path=LOCK)
def verify(root=None):
    return research.verify(root or output(),lock_path=LOCK)
if __name__=='__main__':print(json.dumps(run(),indent=2))

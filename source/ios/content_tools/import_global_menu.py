"""Checksum-pinned original Global menu frames; cache-only, independent of Phase 6 UI lock."""
import json
from pathlib import Path
import import_summon_ui as ui
IOS=ui.IOS
LOCK=Path(__file__).with_name('global-menu-ui.lock.json')
def output():return IOS/'.local/global-menu/versions'/ui.sha(LOCK.read_bytes())[:16]/'GlobalMenu'
def verify(root=None):
 old=ui.LOCK
 try:ui.LOCK=LOCK;return ui.verify(root or output())
 finally:ui.LOCK=old
def run():
 old=ui.LOCK
 try:ui.LOCK=LOCK;return ui.run(output())
 finally:ui.LOCK=old
if __name__=='__main__':print(json.dumps(run()));print(output())

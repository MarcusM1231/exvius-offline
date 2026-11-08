"""Resume controlled source batches; validate selected idle frames before advancing.
No normal-campaign or runtime network access. Run import_unit_animations afterward.
"""
import json,sys
from pathlib import Path
from expand_unit_animations import run,ROOT,LOCK
from import_summon_ui import decode
from unit_animation import parse_cgg,parse_cgs,compose
from PIL import Image
import io
while True:
    ids=run(batch_size=25,budget=5000000)
    if not ids:break
    lock=json.loads(LOCK.read_text());report={}
    for uid in ids:
        members={r['name']:r for r in lock['members'] if r['unit_id']==uid}
        def read(kind):
            row=members[f'unit_{kind}_{uid}'+('.png' if kind=='anime' else '.csv')]
            return decode((Path(__import__('import_content').IOS)/row['cache_path']).read_bytes())
        try:
            texture=Image.open(io.BytesIO(read('anime'))).convert('RGBA');lines=read('cgg').decode().splitlines();seq=parse_cgs(read('idle_cgs').decode(),len(lines))
            if len(seq)>64:raise ValueError('Runtime sequence exceeds 64-frame budget')
            for row in seq:compose(texture,parse_cgg(lines[row['composition']],texture.size)[0],(row['offset_x'],row['offset_y']))
            report[uid]='selected frames reconstructed'
        except ValueError as error:report[uid]='unsupported: '+str(error)
    (ROOT/('validation-%03d.json'%len(lock['units']))).write_text(json.dumps(report,indent=2)+'\n')
    print('VALIDATED',len(report),'unsupported',sum(v.startswith('unsupported') for v in report.values()),flush=True)

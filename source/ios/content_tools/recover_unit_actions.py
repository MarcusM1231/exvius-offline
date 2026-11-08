"""Small Developer research sample; reuse pinned sheets/CGG and bounded CPK reads."""
import json
from pathlib import Path
from import_content import IOS,sha
from import_summon_ui import decode
from range_client import RangeClient
from batch_artwork import coalesce
from expand_unit_animations import restore_locked
LOCK=Path(__file__).with_name('unit-action-research.lock.json')
BASE=Path(__file__).with_name('unit-animation-expanded.lock.json')
ROOT=IOS/'.local/phase6d4c'
IDS=['202000203','100000103','206000103','206000113','100004604','205000703']
ACTIONS=['idle','standby','atk','magic_atk','win_before','win']

def recover():
    if LOCK.exists():
        import expand_unit_animations as recovery
        previous=recovery.LOCK;recovery.LOCK=LOCK
        try:recovery.restore_locked(batch_size=6,budget=100000)
        finally:recovery.LOCK=previous
        return json.loads(LOCK.read_text())
    base=json.loads(BASE.read_text());existing={r['name']:r for r in base['members']};rows=[];sources={};units={};indexes={};missing=[]
    for uid in IDS:
        unit=base['units'][uid];key=unit['source'];record=base['sources'][key];raw=(IOS/record['index_path']).read_bytes()
        if sha(raw)!=record['index_sha256']:raise ValueError('Action CPK index checksum')
        index=json.loads(raw);source=record['source']
        if index['cpk']!=source['name'] or index['cpk_size']!=source['size'] or index['zip_payload_start']!=source['zip_payload_start']:raise ValueError('Action CPK identity')
        entries={r['name']:r for r in index['entries']};sources[key]=record;units[uid]=unit;indexes[key]=entries
        for kind in ['anime','cgg']+[a+'_cgs' for a in ACTIONS]:
            name=f'unit_{kind}_{uid}'+('.png' if kind=='anime' else '.csv');e=entries.get(name)
            if not e:continue
            if not 0<=e['offset_in_cpk']<e['offset_in_cpk']+e['size']<=source['size']:raise ValueError('Action member bounds')
            if name in existing:
                row=existing[name];body=(IOS/row['cache_path']).read_bytes()
                if row['source']!=key or sha(body)!=row['sha256_stored'] or sha(decode(body))!=row['sha256_decoded']:raise ValueError('Existing action dependency mismatch')
                rows.append(row)
            else:missing.append(dict(e,source=key,unit_id=uid,offset=e['offset_in_cpk']))
    client=RangeClient(interval=1.2,max_bytes=100000,journal=ROOT/'action-range-journal.json')
    groups={}
    for r in missing:groups.setdefault(r['source'],[]).append(r)
    for key,entries in groups.items():
        source=sources[key]['source']
        for start,end,members in coalesce(entries,max_gap=1024,max_read=16384):
            body=client.read(source,source['zip_payload_start']+start,end-start)
            for row in members:
                stored=body[row['offset']-start:row['offset']-start+row['size']];unpacked=decode(stored)
                if len(stored)!=row['size'] or len(unpacked)!=row['unpacked']:raise ValueError('Action member lengths')
                p=ROOT/'sources'/key/row['name'];p.parent.mkdir(parents=True,exist_ok=True)
                if p.exists() and p.read_bytes()!=stored:raise ValueError('Changed action cache')
                if not p.exists():p.write_bytes(stored)
                rows.append({**{k:v for k,v in row.items() if k!='offset'},'cache_path':str(p.relative_to(IOS)),'sha256_stored':sha(stored),'sha256_decoded':sha(unpacked)})
    result={'schema':2,'scope':'Developer action/sequence investigation only; production idle lock unchanged','provenance':'Global-targeted preservation; not proof of byte-identical Global retail CDN','base_lock_sha256':sha(BASE.read_bytes()),'sources':sources,'units':units,'members':sorted(rows,key=lambda r:r['name']),'actions':ACTIONS}
    LOCK.write_text(json.dumps(result,indent=2)+'\n');(ROOT/'action-recovery.json').write_text(json.dumps({'network_bytes':client.transferred,'requested_units':IDS,'members':len(rows)},indent=2)+'\n')
    return result
if __name__=='__main__':print(json.dumps({'members':len(recover()['members'])}))

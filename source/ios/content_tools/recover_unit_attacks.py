"""Resumable bounded attack recovery using the existing pinned composition library."""
import argparse,json,time
from pathlib import Path
from import_content import IOS,sha
from import_summon_ui import decode
from expand_unit_animations import plan
from range_client import RangeClient
from batch_artwork import coalesce
LOCK=Path(__file__).with_name('unit-attack-expanded.lock.json')
BASE=Path(__file__).with_name('unit-animation-expanded.lock.json')
ROOT=IOS/'.local/phase6d4d'

def recover(batch_size=25,budget=1000000):
    if not 1<=batch_size<=30:raise ValueError('Batch must contain 1–30 IDs')
    ROOT.mkdir(parents=True,exist_ok=True)
    base=json.loads(BASE.read_text());sources,indexes,inventory=plan()
    if base['sources']!=sources:raise ValueError('Pinned source index changed')
    for key,r in sources.items():
        if sha((IOS/r['index_path']).read_bytes())!=r['index_sha256']:raise ValueError('Index checksum')
    lock=json.loads(LOCK.read_text()) if LOCK.exists() else {**base,'base_lock_sha256':sha(BASE.read_bytes()),'actions':['idle','standby','atk'],'attack_reviewed':[]}
    if lock['base_lock_sha256']!=sha(BASE.read_bytes()):raise ValueError('Idle foundation changed')
    for row in lock['members']:
        raw=(IOS/row['cache_path']).read_bytes()
        if len(raw)!=row['size'] or sha(raw)!=row['sha256_stored'] or sha(decode(raw))!=row['sha256_decoded']:raise ValueError('Pinned cache changed')
    order=['100005404']+[uid for uid in sorted(inventory) if uid!='100005404']
    pending=[uid for uid in order if uid not in lock['attack_reviewed']][:batch_size]
    known={r['name'] for r in lock['members']};research=json.loads(Path(__file__).with_name('unit-action-research.lock.json').read_text());reused={r['name']:r for r in research['members']}
    groups={};rows=[]
    for uid in pending:
        key=inventory[uid]['source'];name=f'unit_atk_cgs_{uid}.csv'
        if key is None or name not in indexes[key] or name in known:continue
        e=indexes[key][name];src=sources[key]['source']
        if not 0<=e['offset_in_cpk']<e['offset_in_cpk']+e['size']<=src['size']:raise ValueError('Member bounds')
        if name in reused:
            r=reused[name]
            if r['source']!=key:raise ValueError('Research source mismatch')
            rows.append(r);continue
        row=dict(e,source=key,unit_id=uid,offset=e['offset_in_cpk'])
        p=ROOT/'sources'/key/name
        if p.exists():
            data=p.read_bytes()
            if len(data)!=e['size'] or len(decode(data))!=e['unpacked']:raise ValueError('Partial recovery cache')
            row.update(cache_path=str(p.relative_to(IOS)),sha256_stored=sha(data),sha256_decoded=sha(decode(data)));rows.append({k:v for k,v in row.items() if k!='offset'})
        else:groups.setdefault(key,[]).append(row)
    client=RangeClient(interval=1,max_bytes=budget,journal=ROOT/'ranges'/f'{time.time_ns()}.json')
    for key,entries in groups.items():
        for start,end,members in coalesce(entries,max_gap=16384,max_read=262144):
            body=client.read(sources[key]['source'],sources[key]['source']['zip_payload_start']+start,end-start)
            for row in members:
                data=body[row['offset']-start:row['offset']-start+row['size']];decoded=decode(data)
                if len(data)!=row['size'] or len(decoded)!=row['unpacked']:raise ValueError('Member length')
                p=ROOT/'sources'/key/row['name'];p.parent.mkdir(parents=True,exist_ok=True)
                if p.exists() and p.read_bytes()!=data:raise ValueError('Existing source changed')
                if not p.exists():p.write_bytes(data)
                rows.append({**{k:v for k,v in row.items() if k!='offset'},'cache_path':str(p.relative_to(IOS)),'sha256_stored':sha(data),'sha256_decoded':sha(decoded)})
    lock['members']=sorted(lock['members']+rows,key=lambda r:r['name']);lock['attack_reviewed']+=pending
    tmp=LOCK.with_suffix('.pending');tmp.write_text(json.dumps(lock,indent=2)+'\n');tmp.replace(LOCK)
    print(json.dumps({'reviewed':len(lock['attack_reviewed']),'batch':len(pending),'network_bytes':client.transferred}),flush=True)
    return pending
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--all',action='store_true');p.add_argument('--restore',action='store_true');a=p.parse_args()
    if a.restore:
        import expand_unit_animations as recovery
        recovery.LOCK=LOCK;recovery.ROOT=ROOT
        while recovery.restore_locked(batch_size=25,budget=4000000):
            if not a.all:break
    else:
        while recover():
            if not a.all:break

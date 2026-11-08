"""Catalog-driven bounded animation batches; resumable source pins, no campaign access."""
import argparse,json,time
from pathlib import Path
from import_content import IOS,sha,default_output
from import_summon_ui import decode
from range_client import RangeClient,RangeError
from batch_artwork import coalesce
ROOT=IOS/'.local/phase6d4b'
LOCK=Path(__file__).with_name('unit-animation-expanded.lock.json')

def plan():
    content=json.loads(Path(__file__).with_name('content.lock.json').read_text())
    catalog=json.loads((default_output()/'catalog.json').read_text())['units']
    sources={};indexes={}
    originals=json.loads(Path(__file__).with_name('unit_sources.lock.json').read_text())['sources']
    for source in originals:
        key=source['archive']+'-'+Path(source['name']).name
        p=IOS/'.local/unit-content/discovery'/(key+'.json')
        if not p.exists():continue
        raw=p.read_bytes();idx=json.loads(raw)
        if idx['cpk']!=source['name'] or idx['cpk_size']!=source['size']:raise ValueError('Index identity')
        start=idx['zip_payload_start']
        if not source['offset']+30<=start or start+source['size']>source['archive_size']:raise ValueError('Archive bounds')
        pinned=content['range_sources'].get(key)
        if pinned and pinned['zip_payload_start']!=start:raise ValueError('Pinned payload mismatch')
        sources[key]={'source':dict(source,zip_payload_start=start),'index_path':str(p.relative_to(IOS)),'index_sha256':sha(raw)}
        indexes[key]={e['name']:e for e in idx['entries']}
    prior=json.loads(Path(__file__).with_name('unit-animation-sources.lock.json').read_text())
    priorids={e['name'].split('_')[-1].split('.')[0] for e in prior['members']}
    target_ids=set(content['targets']['demo_ids'])|priorids
    inventory={}
    for uid,u in sorted(catalog.items()):
        if uid not in target_ids:continue
        candidates=[]
        for key,entries in indexes.items():
            names=[f'unit_anime_{uid}.png',f'unit_cgg_{uid}.csv',f'unit_idle_cgs_{uid}.csv']
            if all(n in entries for n in names):candidates.append(key)
        preferred=next((a.get('range_source') for a in content['artwork'] if a['unit_id']==uid),None)
        key=('data-008-Ver24_unit1_common.cpk' if uid in priorids else preferred) if candidates else None
        if key not in candidates:key=candidates[0] if candidates else None
        e=indexes.get(key,{})
        inventory[uid]={'name':u['name'],'master_id':uid,'static_artwork':u.get('artwork'), 'source':key,
          'source_archive':sources[key]['source']['archive'] if key else None,'container':sources[key]['source']['name'] if key else None,
          'banner_pool_ids':[b for b,pool in content['targets']['banner_pools'].items() if uid in pool],
          'availability':{kind:(f'unit_{kind}_{uid}'+('.png' if kind=='anime' else '.csv')) in e for kind in ['anime','cgg','idle_cgs','standby_cgs']},
          'actions':[n for n in e if n.endswith('_'+uid+'.csv') and '_cgs_' in n],
          'estimated_source_bytes':sum(e[n]['size'] for n in [f'unit_anime_{uid}.png',f'unit_cgg_{uid}.csv',f'unit_idle_cgs_{uid}.csv'] if n in e),
          'is_target':uid in content['targets']['demo_ids'],
          'status':'indexed' if key else 'missing exact-ID resource set'}
    return sources,indexes,inventory

def run(ids=None,batch_size=25,budget=4000000):
    ROOT.mkdir(parents=True,exist_ok=True);sources,indexes,inventory=plan()
    lock=json.loads(LOCK.read_text()) if LOCK.exists() else {'schema':2,'provenance':'Global-targeted preservation; retail CDN identity and acquisition routing unverified','sources':sources,'members':[],'units':{}}
    if lock['sources']!=sources:raise ValueError('Source index changed; review before resuming')
    for member in lock['members']:
        raw=(IOS/member['cache_path']).read_bytes()
        if len(raw)!=member['size'] or sha(raw)!=member['sha256_stored']:raise ValueError('Previously pinned member changed')
    requested=list(ids or ([i for i in ["202000203","100000103","206000103","206000113"] if i in inventory]+[i for i in inventory if i not in {"202000203","100000103","206000103","206000113"}]))
    if len(set(requested))!=len(requested) or any(i not in inventory for i in requested):raise ValueError('Unknown/duplicate exact ID')
    pending=[i for i in requested if i not in lock['units'] and inventory[i]['source']][:batch_size]
    planned=[]
    for uid in pending:
        key=inventory[uid]['source'];entries=indexes[key]
        kinds=['anime','cgg','idle_cgs']+(['standby_cgs'] if uid in ['202000203','100000103','206000103','206000113'] else [])
        for kind in kinds:
            name=f'unit_{kind}_{uid}'+('.png' if kind=='anime' else '.csv');e=entries[name]
            if not 0<=e['offset_in_cpk']<e['offset_in_cpk']+e['size']<=sources[key]['source']['size']:raise ValueError('Member bounds')
            planned.append(dict(e,source=key,unit_id=uid,offset=e['offset_in_cpk']))
    client=RangeClient(interval=0.75,max_bytes=budget,journal=ROOT/'ranges'/(str(time.time_ns())+'.json'))
    grouped={}
    for row in planned:
        p=ROOT/'sources'/row['source']/row['name'];old=IOS/'.local/phase6d4/sources'/row['name']
        if not p.exists() and old.exists() and row['source']=='data-008-Ver24_unit1_common.cpk':
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old.read_bytes())
        if not p.exists():grouped.setdefault(row['source'],[]).append(row)
    for key,rows in grouped.items():
        for start,end,members in coalesce(rows,max_gap=16384,max_read=1024*1024):
            body=None
            for attempt in range(2):
                try:body=client.read(sources[key]['source'],sources[key]['source']['zip_payload_start']+start,end-start);break
                except RangeError:
                    # Retry only a zero-byte connection failure, once. Never
                    # retry rate limits, ignored ranges, or partial responses.
                    last=client.requests[-1] if client.requests else {}
                    if attempt or last.get('http_status')!='000' or last.get('received')!=0:raise
                    time.sleep(2)
                except (TimeoutError,OSError):
                    if attempt:raise
                    time.sleep(2)
            for row in members:
                p=ROOT/'sources'/key/row['name'];p.parent.mkdir(parents=True,exist_ok=True)
                data=body[row['offset']-start:row['offset']-start+row['size']]
                if len(data)!=row['size']:raise ValueError('Short member')
                decoded=decode(data)
                if len(decoded)!=row['unpacked']:raise ValueError('Decoded size')
                p.write_bytes(data)
    for row in planned:
        data=(ROOT/'sources'/row['source']/row['name']).read_bytes();decoded=decode(data)
        if len(data)!=row['size'] or len(decoded)!=row['unpacked']:raise ValueError('Cached size')
        row={k:v for k,v in row.items() if k!='offset'};row.update(sha256_stored=sha(data),sha256_decoded=sha(decoded),cache_path=str((ROOT/'sources'/row['source']/row['name']).relative_to(IOS)))
        lock['members'].append(row)
    for uid in pending:lock['units'][uid]=inventory[uid]
    temp=LOCK.with_suffix('.pending');temp.write_text(json.dumps(lock,indent=2)+'\n');temp.replace(LOCK)
    for uid in inventory:
        if uid in lock['units']:inventory[uid]['status']='recovered; parser validation pending'
    (ROOT/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (ROOT/('batch-%03d.json'%len(lock['units']))).write_text(json.dumps({'selected':pending,'network_bytes':client.transferred,'requests':client.requests},indent=2)+'\n')
    print(json.dumps({'recovered_ids':len(lock['units']),'batch':len(pending),'indexed_ids':sum(bool(v['source']) for v in inventory.values()),'network_bytes':client.transferred}),flush=True)
    return pending
def restore_locked(batch_size=25,budget=5000000):
    """Rehydrate missing pinned members without changing the reviewed lock."""
    lock=json.loads(LOCK.read_text());missing=[];indexes={}
    for key,record in lock['sources'].items():
        raw=(IOS/record['index_path']).read_bytes()
        if sha(raw)!=record['index_sha256']:raise ValueError('Pinned index checksum')
        indexes[key]={e['name']:e for e in json.loads(raw)['entries']}
    units=[]
    for row in lock['members']:
        source=lock['sources'][row['source']]['source'];entry=indexes[row['source']][row['name']]
        if any(row[k]!=entry[k] for k in ('size','unpacked','offset_in_cpk')):raise ValueError('Pinned member/index mismatch')
        if not 0<=row['offset_in_cpk']<row['offset_in_cpk']+row['size']<=source['size']:raise ValueError('Pinned bounds')
        p=IOS/row['cache_path']
        if p.exists():
            if len(p.read_bytes())!=row['size'] or sha(p.read_bytes())!=row['sha256_stored']:raise ValueError('Refusing altered cache')
        else:
            if row['unit_id'] not in units and len(units)<batch_size:units.append(row['unit_id'])
            if row['unit_id'] in units:missing.append(row)
    client=RangeClient(interval=0.75,max_bytes=budget,journal=ROOT/'ranges'/(str(time.time_ns())+'.json'))
    grouped={}
    for row in missing:grouped.setdefault(row['source'],[]).append(dict(row,offset=row['offset_in_cpk']))
    for key,rows in grouped.items():
        source=lock['sources'][key]['source']
        for start,end,members in coalesce(rows,max_gap=16384,max_read=1024*1024):
            raw=client.read(source,source['zip_payload_start']+start,end-start)
            for row in members:
                body=raw[row['offset']-start:row['offset']-start+row['size']];decoded=decode(body)
                if len(body)!=row['size'] or sha(body)!=row['sha256_stored'] or len(decoded)!=row['unpacked'] or sha(decoded)!=row['sha256_decoded']:raise ValueError('Restore checksum')
                p=IOS/row['cache_path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    print(json.dumps({'restored_members':len(missing),'network_bytes':client.transferred}))
    return len(missing)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ids');p.add_argument('--restore',action='store_true');p.add_argument('--batch-size',type=int,default=25);p.add_argument('--budget',type=int,default=4000000);a=p.parse_args()
    if not 1<=a.batch_size<=30:raise ValueError('Batch must contain 1–30 IDs')
    if a.restore:restore_locked(a.batch_size,a.budget)
    else:run(a.ids.split(',') if a.ids else None,a.batch_size,a.budget)

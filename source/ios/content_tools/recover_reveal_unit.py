"""Recover four exact-ID Maria research members; retain the pinned Phase 5 index."""
import json
from pathlib import Path
from import_content import IOS,sha
from import_summon_ui import decode
from range_client import RangeClient
LOCK=Path(__file__).with_name('reveal-unit-research.lock.json')
CACHE=IOS/'.local/phase6d1'

def run(client=None):
    lock=json.loads(LOCK.read_text());raw=(IOS/lock['index_path']).read_bytes()
    if sha(raw)!=lock['index_sha256']:raise ValueError('Unit index checksum mismatch')
    index=json.loads(raw);source=lock['source']
    if index['cpk']!=source['name'] or index['cpk_size']!=source['size'] or index['zip_payload_start']!=source['zip_payload_start']:raise ValueError('Unit index identity mismatch')
    if not source['offset']+30<=source['zip_payload_start'] or source['zip_payload_start']+source['size']>source['archive_size']:raise ValueError('ZIP bounds')
    entries={r['name']:r for r in index['entries']}
    client=client or RangeClient(interval=1.2,max_bytes=40000,journal=CACHE/'unit-recovery-journal.json')
    for row in lock['members']:
        if any(entries.get(row['name'],{}).get(k)!=row[k] for k in ['name','offset_in_cpk','size','unpacked']):raise ValueError('Member identity mismatch')
        if not 0<=row['offset_in_cpk']<row['offset_in_cpk']+row['size']<=source['size']:raise ValueError('CPK bounds')
        p=CACHE/'maria'/row['name'];body=p.read_bytes() if p.exists() else client.read(source,source['zip_payload_start']+row['offset_in_cpk'],row['size'])
        if len(body)!=row['size'] or sha(body)!=row['sha256_stored']:raise ValueError('Unit source checksum')
        unpacked=decode(body)
        if len(unpacked)!=row['unpacked'] or sha(unpacked)!=row['sha256_decoded']:raise ValueError('Unit decoded checksum')
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():
            with p.open('xb') as f:f.write(body)
    return {'members':len(lock['members']),'network_bytes':getattr(client,'transferred',0)}
if __name__=='__main__':print(json.dumps(run(),indent=2))

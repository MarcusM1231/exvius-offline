"""Bounded recovery of exact-ID animation research files; never touches saves."""
import json
from pathlib import Path
from import_content import IOS, sha
from import_summon_ui import decode
from range_client import RangeClient
LOCK = Path(__file__).with_name('unit-animation-sources.lock.json')
CACHE = IOS / '.local/phase6d4/sources'

def recover():
    lock = json.loads(LOCK.read_text())
    original = json.loads(Path(__file__).with_name('reveal-unit-research.lock.json').read_text())
    raw = (IOS / original['index_path']).read_bytes()
    if sha(raw) != original['index_sha256']: raise ValueError('CPK index checksum')
    index = json.loads(raw)
    source = original['source']
    if index['cpk'] != source['name'] or index['cpk_size'] != source['size'] or index['zip_payload_start'] != source['zip_payload_start']: raise ValueError('CPK identity')
    entries = {r['name']: r for r in index['entries']}
    client = RangeClient(interval=1.2, max_bytes=400000, journal=IOS/'.local/phase6d4/range-journal.json')
    for row in lock['members']:
        e = entries[row['name']]
        if any(e[k] != row[k] for k in ('offset_in_cpk','size','unpacked')): raise ValueError('Index member mismatch')
        if not 0 <= e['offset_in_cpk'] < e['offset_in_cpk']+e['size'] <= source['size']: raise ValueError('CPK bounds')
        p = CACHE/row['name']
        old = IOS/'.local/phase6d1/maria'/row['name']
        body = p.read_bytes() if p.exists() else old.read_bytes() if old.exists() else client.read(source,source['zip_payload_start']+e['offset_in_cpk'],e['size'])
        if len(body)!=row['size'] or sha(body)!=row['sha256_stored']: raise ValueError('Stored checksum')
        decoded = decode(body)
        if len(decoded)!=row['unpacked'] or sha(decoded)!=row['sha256_decoded']: raise ValueError('Decoded checksum')
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists(): p.write_bytes(body)
    return {'members':len(lock['members']),'network_bytes':client.transferred}
if __name__=='__main__': print(json.dumps(recover(),indent=2))

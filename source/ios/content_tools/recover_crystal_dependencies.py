"""Recover only pinned shared crystal dependencies by exact bounded archive ranges.

No full ZIP/CPK download. Existing cache bytes must match; never overwrite them.
"""
import json
from pathlib import Path
from import_summon_ui import decode
from import_content import IOS, sha
from range_client import RangeClient

LOCK=Path(__file__).with_name('crystal-dependencies.lock.json')
CACHE=IOS/'.local/phase6c1'

def run(client=None):
    lock=json.loads(LOCK.read_text())
    client=client or RangeClient(interval=1.1,max_bytes=2*1024**2,journal=CACHE/'recovery-range-journal.json')
    for row in lock['members']:
        path=CACHE/row['cache_path']
        if path.exists():body=path.read_bytes()
        else:
            source=lock['sources'][row['source']]
            if not 0<=row['offset_in_cpk']<source['cpk_size'] or row['offset_in_cpk']+row['size']>source['cpk_size']:
                raise ValueError('Pinned crystal range outside CPK')
            body=client.read(source,source['zip_payload_start']+row['offset_in_cpk'],row['size'])
        if len(body)!=row['size'] or sha(body)!=row['sha256_stored']:raise ValueError('Pinned crystal member checksum mismatch')
        unpacked=decode(body)
        if len(unpacked)!=row['unpacked'] or sha(unpacked)!=row['sha256_decoded']:raise ValueError('Decoded crystal member checksum mismatch')
        if not path.exists():
            path.parent.mkdir(parents=True,exist_ok=True)
            # Exclusive creation protects any concurrently created local file.
            with path.open('xb') as stream:stream.write(body)
    return {'members':len(lock['members']),'network_bytes':getattr(client,'transferred',0)}

if __name__=='__main__':print(json.dumps(run(),indent=2))

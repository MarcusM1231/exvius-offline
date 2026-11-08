"""Bounded retrieval of five pinned stage research resources; refuses changed cache/index."""
import json
from pathlib import Path
from import_content import IOS, sha
from import_summon_ui import decode
from range_client import RangeClient
import expand_artwork as discovery

LOCK=Path(__file__).with_name('reveal-stage.lock.json')
CACHE=IOS/'.local/phase6d1'

def run(client=None):
    lock=json.loads(LOCK.read_text())
    client=client or RangeClient(interval=1.1,max_bytes=512*1024,journal=CACHE/'recovery-journal.json')
    indexes={}
    previous=discovery.CACHE
    try:
        discovery.CACHE=CACHE
        for key,source in lock['range_sources'].items():
            index,record=discovery.read_index(source,client)
            indexes[key]={r['name']:r for r in index['entries']}
            if record['index_sha256']!=source['index_sha256'] or record['toc_sha256']!=source['toc_sha256']:
                raise ValueError('Research archive index checksum changed')
    finally:discovery.CACHE=previous
    for row in lock['members']:
        source=lock['range_sources'][row['source']]
        indexed=indexes[row['source']].get(row['name'])
        if not indexed or any(indexed[k]!=row[k] for k in ['name','offset_in_cpk','size','unpacked']):raise ValueError('Research member identity disagrees with index')
        if row['size']<=0 or row['offset_in_cpk']<0 or row['offset_in_cpk']+row['size']>source['cpk_size']:
            raise ValueError('Research member bounds')
        path=CACHE/row['cache_path']
        body=path.read_bytes() if path.exists() else client.read(source,source['zip_payload_start']+row['offset_in_cpk'],row['size'])
        if len(body)!=row['size'] or sha(body)!=row['sha256_stored']:raise ValueError('Research stored checksum')
        unpacked=decode(body)
        if len(unpacked)!=row['unpacked'] or sha(unpacked)!=row['sha256_decoded']:raise ValueError('Research decoded checksum')
        if not path.exists():
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as f:f.write(body)
    return {'members':len(lock['members']),'network_bytes':getattr(client,'transferred',0)}

if __name__=='__main__':print(json.dumps(run(),indent=2))

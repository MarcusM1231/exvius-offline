"""Discover exact-ID static sprites and publish validated, resumable offline batches."""
import argparse
import csv
import io
import json
from pathlib import Path
import re
import struct
import sys
import tempfile

sys.dont_write_bytecode = True
from cpk_reader import utf
from import_content import IOS, LOCK, PNG_CACHE, DEFAULT_SOURCE, default_output, load_lock, sha, build_catalog, validate_png
from batch_artwork import coalesce, cache_image, publish_batch
from range_client import RangeClient, RangeError

CACHE = IOS / '.local/unit-content'
SOURCES = Path(__file__).with_name('unit_sources.lock.json')


def targets():
    sys.path.insert(0, str(IOS / 'prototype'))
    from demo_data import prepare
    from summon_service import SummonService
    with tempfile.TemporaryDirectory(dir=IOS / '.local', prefix='art-targets-') as temp:
        root = Path(temp)
        data = prepare(root / 'data')
        service = SummonService(data, root / 'planning-only.json', demo=True)
        ids = sorted(json.loads(line)['3HriTp6B'] for line in (data / 'mst_decoded/F_UNIT_MST.ndjson').read_text().splitlines())
        pools, weights = {}, {}
        for banner in service.banners():
            rows = service.details(banner['id'])['base_pool']
            pools[banner['id']] = sorted({row['unit_id'] for row in rows})
            for row in rows:
                uid = row['unit_id']
                weights[uid] = weights.get(uid, 0) + row['probability']
    return {'demo_ids': ids, 'banner_pools': pools, 'priority_base_weights': weights,
            'note': 'Read from existing SummonService.details; base weights are not guaranteed-slot probabilities.'}


def source_key(source):
    return source['archive'] + '-' + Path(source['name']).name


def read_index(source, client):
    path = CACHE / 'discovery' / (source_key(source) + '.json')
    if path.exists():
        content = path.read_bytes()
        index = json.loads(content)
        if index['archive'] != source['archive'] or index['cpk'] != source['name'] or index['cpk_size'] != source['size']:
            raise ValueError('Cached CPK index does not match pinned source')
    else:
        prefix = client.read(source, source['offset'], min(4096, source['size']))
        if prefix[:4] != b'PK\x03\x04' or source['method'] != 0:
            raise ValueError('Expected a stored CPK ZIP member')
        name_size, extra_size = struct.unpack_from('<HH', prefix, 26)
        if prefix[30:30+name_size].decode() != source['name']:
            raise ValueError('ZIP filename mismatch')
        shift = 30 + name_size + extra_size
        start = source['offset'] + shift
        header = prefix[shift:]
        if header[:4] != b'CPK ':
            raise ValueError('Expected CPK signature')
        length = struct.unpack_from('<Q', header, 8)[0]
        if length + 16 > len(header):
            header = client.read(source, start, length + 16)
        info = utf(header[16:16+length])[0]
        toc_offset, toc_size = info['TocOffset'], info['TocSize']
        if toc_offset < 0 or toc_offset + toc_size > source['size']:
            raise ValueError('Invalid CPK TOC bounds')
        toc = client.read(source, start+toc_offset, toc_size)
        if toc[:4] != b'TOC ':
            raise ValueError('Expected CPK TOC signature')
        length = struct.unpack_from('<Q', toc, 8)[0]
        rows = utf(toc[16:16+length])
        if len(rows) != info['Files']:
            raise ValueError('CPK file count mismatch')
        base = min(toc_offset, info['ContentOffset'])
        entries = []
        for row in rows:
            name = '/'.join(str(row.get(k, '')) for k in ('DirName', 'FileName') if row.get(k))
            entries.append({'name': name, 'offset_in_cpk': row['FileOffset']+base,
                            'size': row['FileSize'], 'unpacked': row['ExtractSize']})
        index = {'archive': source['archive'], 'cpk': source['name'], 'cpk_size': source['size'],
                 'zip_payload_start': start, 'toc_sha256': sha(toc), 'entries': entries}
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (json.dumps(index, indent=2)+'\n').encode()
        path.write_bytes(content)
    start = index['zip_payload_start']
    if start < source['offset']+30 or start+source['size'] > source['archive_size']:
        raise ValueError('Invalid cached ZIP/CPK bounds')
    record = dict(source, zip_payload_start=start, cpk_size=source['size'], index_sha256=sha(content))
    if 'toc_sha256' in index:
        record['toc_sha256'] = index['toc_sha256']
    else:
        record['index_provenance'] = 'Reused Phase 5 read-only CPK index; PNG bytes checked individually.'
    names = set()
    for entry in index['entries']:
        if entry['name'] in names:
            raise ValueError('Duplicate filename in CPK index')
        names.add(entry['name'])
        if entry['offset_in_cpk'] < 0 or entry['offset_in_cpk'] + entry['size'] > source['size']:
            raise ValueError('CPK file bounds mismatch')
    return index, record


def coverage(target, stopped=None):
    lock = load_lock()
    imported = {r['unit_id'] for r in lock['artwork']}
    demo, pools = set(target['demo_ids']), target['banner_pools']
    union = set().union(*(set(v) for v in pools.values()))
    root = default_output()
    image_bytes = sum(p.stat().st_size for p in (root/'sprites').glob('*.png'))
    baseline = CACHE/'UnitContent'
    old_size = sum(p.stat().st_size for p in baseline.rglob('*') if p.is_file()) if baseline.exists() else 0
    size = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    report = {'imported_sprites': len(imported), 'demo_ids': len(demo), 'matched_demo_ids': len(imported&demo),
              'banner_pool_ids': len(union), 'matched_banner_pool_ids': len(imported&union),
              'missing_demo_ids': sorted(demo-imported), 'missing_banner_ids': sorted(union-imported),
              'per_banner': {k:{'pool_ids':len(v),'with_artwork':len(set(v)&imported)} for k,v in pools.items()},
              'png_bytes': image_bytes, 'content_bundle_bytes': size, 'phase5b_content_bytes': old_size,
              'content_size_increase_bytes': size-old_size, 'active_bundle': str(root),
              'lock_sha256': sha(LOCK.read_bytes()), 'stopped_reason': stopped}
    folder = CACHE/'reports'
    folder.mkdir(exist_ok=True)
    (folder/'coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    units = build_catalog(DEFAULT_SOURCE)['units']
    text = io.StringIO()
    writer = csv.writer(text)
    writer.writerow(['master_id','name','in_demo','in_banner_pool','has_artwork'])
    for uid in sorted(demo|union):
        writer.writerow([uid,units.get(uid,{}).get('name'),uid in demo,uid in union,uid in imported])
    (folder/'coverage.csv').write_text(text.getvalue())
    return report


def fetch_candidates(candidates, source_records, client):
    results = []
    for key in sorted({row['range_source'] for row in candidates}):
        source = source_records[key]
        rows = [r for r in candidates if r['range_source'] == key]
        for start,end,members in coalesce(rows):
            body = client.read(source,source['zip_payload_start']+start,end-start)
            for row in members:
                image = body[row['offset']-start:row['offset']-start+row['size']]
                info = validate_png(image)
                row = dict(row,sha256=sha(image),png=info)
                cache_image(PNG_CACHE,row['sha256'],image)
                results.append(row)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch-size',type=int,default=48)
    parser.add_argument('--max-new',type=int,default=423)
    parser.add_argument('--budget-mib',type=int,default=16)
    args=parser.parse_args()
    if not 1 <= args.batch_size <= 64 or not 1 <= args.max_new <= 423 or not 1 <= args.budget_mib <= 32:
        parser.error('Use batch-size 1–64, max-new 1–423 and budget-mib 1–32')
    target=targets()
    wanted=set(target['demo_ids'])
    catalog=build_catalog(DEFAULT_SOURCE)['units']
    if not wanted <= set(catalog):
        raise ValueError('Demo IDs missing from verified Global master table')
    sources=json.loads(SOURCES.read_text())['sources']
    # Reuse earlier indexes first, then old main packs before shift/tutorial packs.
    def rank(s):
        known=(CACHE/'discovery'/(source_key(s)+'.json')).exists()
        number=int(re.search(r'_unit(\d+)',s['name']).group(1))
        return (not known, '_tutorial' in s['name'], '_sg_' in s['name'],number,s['name'])
    client=RangeClient(max_bytes=args.budget_mib*1024**2,journal=CACHE/'reports/last-network-run.json')
    new_count=0
    stopped=None
    try:
        for source in sorted(sources,key=rank):
            have={r['unit_id'] for r in load_lock()['artwork']}
            if wanted <= have or new_count >= args.max_new:
                break
            index,record=read_index(source,client)
            key=source_key(source)
            candidates=[]
            for entry in index['entries']:
                match=re.fullmatch(r'unit_ills_(\d+)\.png',entry['name'])
                if not match or match[1] not in wanted-have:
                    continue
                if entry['size'] != entry['unpacked']:
                    continue
                candidates.append({'unit_id':match[1],'file':entry['name'],'range_source':key,
                                   'offset':entry['offset_in_cpk'],'size':entry['size'],'unpacked':entry['unpacked']})
            candidates.sort(key=lambda r:(-target['priority_base_weights'].get(r['unit_id'],0),r['unit_id']))
            while candidates and new_count < args.max_new:
                batch=candidates[:min(args.batch_size,args.max_new-new_count)]
                candidates=candidates[len(batch):]
                validated=fetch_candidates(batch,{key:record},client)
                publish_batch(validated,{key:record},target)
                new_count+=len(validated)
                result=coverage(target)
                batch_dir=CACHE/'batches'
                batch_dir.mkdir(exist_ok=True)
                (batch_dir/(result['lock_sha256'][:16]+'.json')).write_text(json.dumps({'unit_ids':[r['unit_id'] for r in validated],'lock_sha256':result['lock_sha256'],'bundle':result['active_bundle'],'network_bytes_this_run':client.transferred},indent=2)+'\n')
                print('Validated batch: +%s; artwork %s/%s demo IDs; PNG bytes %s; transferred %s' % (len(validated),result['matched_demo_ids'],result['demo_ids'],result['png_bytes'],client.transferred),flush=True)
    except (RangeError,ValueError,OSError) as error:
        stopped=str(error)
        print('STOPPED:',stopped,flush=True)
    result=coverage(target,stopped)
    print(json.dumps({k:result[k] for k in ('imported_sprites','matched_demo_ids','matched_banner_pool_ids','content_size_increase_bytes','stopped_reason')},indent=2))
    return 0 if result['matched_demo_ids']>3 or not stopped else 1


if __name__=='__main__':
    raise SystemExit(main())

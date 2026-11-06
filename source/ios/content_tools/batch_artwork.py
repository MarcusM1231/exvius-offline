"""Build-time-only PNG range reads, validated caches, and atomic lock/bundle batches."""
import json
from pathlib import Path
import tempfile

from import_content import (LOCK, PNG_CACHE, DEFAULT_SOURCE, default_output, import_content,
                            load_lock, sha, validate_png, verify_bundle)


def validate_artwork(row, body):
    if row['file'] != 'unit_ills_' + row['unit_id'] + '.png':
        raise ValueError('Artwork filename/master-ID mismatch')
    if len(body) != row['size'] or sha(body) != row['sha256']:
        raise ValueError('Artwork checksum/length mismatch: ' + row['unit_id'])
    return validate_png(body)


def coalesce(rows, max_gap=4096, max_read=128*1024):
    groups = []
    for row in sorted(rows, key=lambda x: x['offset']):
        start, end = row['offset'], row['offset'] + row['size']
        if not row['size'] or row['size'] > max_read or start < 0:
            raise ValueError('Unsupported sprite range')
        if groups and start < groups[-1][1]:
            raise ValueError('Overlapping artwork ranges')
        if groups and start - groups[-1][1] <= max_gap and end - groups[-1][0] <= max_read:
            groups[-1][1] = end
            groups[-1][2].append(row)
        else:
            groups.append([start, end, [row]])
    return groups


def cache_image(cache, digest, body):
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (digest + '.png')
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError('Existing PNG cache checksum mismatch')
        return
    with tempfile.NamedTemporaryFile(dir=cache, delete=False) as temporary:
        temporary.write(body)
        pending = Path(temporary.name)
    pending.rename(path)


def fetch_locked_images(lock, client, cache=PNG_CACHE):
    grouped = {}
    for art in lock['artwork']:
        if 'range_source' not in art:
            continue
        path = Path(cache) / (art['sha256'] + '.png')
        if path.exists():
            validate_artwork(art, path.read_bytes())
        else:
            grouped.setdefault(art['range_source'], []).append(art)
    for key, rows in grouped.items():
        source = lock['range_sources'][key]
        for start, end, members in coalesce(rows):
            if end > source['cpk_size']:
                raise ValueError('Artwork range exceeds CPK')
            body = client.read(source, source['zip_payload_start'] + start, end-start)
            for row in members:
                image = body[row['offset']-start:row['offset']-start+row['size']]
                validate_artwork(row, image)
                cache_image(cache, row['sha256'], image)


def publish_batch(artwork, sources, targets):
    """PNG bytes must already be validated/cached; publish only a complete valid batch."""
    old_bytes = LOCK.read_bytes()
    old = load_lock()
    existing = {r['unit_id']: r for r in old['artwork']}
    if len({r['unit_id'] for r in artwork}) != len(artwork):
        raise ValueError('Duplicate unit IDs in batch')
    new = json.loads(old_bytes)
    new.setdefault('range_sources', {}).update(sources)
    for row in artwork:
        if row['unit_id'] in existing:
            if existing[row['unit_id']]['sha256'] != row['sha256']:
                raise ValueError('Conflicting artwork for an existing unit ID')
            continue
        validate_artwork(row, (PNG_CACHE / (row['sha256'] + '.png')).read_bytes())
        new['artwork'].append(row)
    new['artwork'].sort(key=lambda r: r['unit_id'])
    new['targets'] = targets
    pending = LOCK.with_suffix('.pending')
    try:
        pending.write_text(json.dumps(new, indent=2) + '\n')
        pending.replace(LOCK)
        receipt = import_content(DEFAULT_SOURCE)
        verify_bundle(default_output())
    except Exception:
        LOCK.write_bytes(old_bytes)
        pending.unlink(missing_ok=True)
        raise
    return receipt

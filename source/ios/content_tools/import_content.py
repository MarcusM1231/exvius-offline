"""Build-time import of pinned metadata and exact-ID static PNGs. Never opens saves."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import zlib

sys.dont_write_bytecode = True
from cpk_reader import index
from png_validation import png_info

IOS = Path(__file__).resolve().parents[1]
LOCK = Path(__file__).with_name('content.lock.json')
DEFAULT_SOURCE = IOS / '.local/unit-content/sources'
PNG_CACHE = IOS / '.local/unit-content/png-cache'

def default_output():
    lock = json.loads(LOCK.read_text())
    if lock.get('range_sources'):
        return IOS / '.local/unit-content/versions' / hashlib.sha256(LOCK.read_bytes()).hexdigest()[:16] / 'UnitContent'
    return IOS / '.local/unit-content/UnitContent'

DEFAULT_OUTPUT = default_output()


def sha(body):
    return hashlib.sha256(body).hexdigest()


def load_lock():
    lock = json.loads(LOCK.read_text(encoding='utf-8'))
    ids = [row['unit_id'] for row in lock['artwork']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate artwork unit ID in content lock')
    return lock


def validate_source(body, entry):
    if len(body) != entry['size'] or sha(body) != entry['sha256'] or zlib.crc32(body) != entry['crc32']:
        raise ValueError('Pinned source checksum mismatch: ' + entry['name'])


def download_member(entry, destination, client=None):
    """Read only one pinned member using the same throttled, bounded client."""
    from range_client import RangeClient
    client = client or RangeClient()
    def read(offset, length):
        return client.read(entry, offset, length)
    header = read(entry['offset'], 30)
    if header[:4] != b'PK\x03\x04':
        raise ValueError('Invalid ZIP local header')
    name_size, extra_size = struct.unpack_from('<HH', header, 26)
    name = read(entry['offset'] + 30, name_size + extra_size)
    if name[:name_size].decode() != entry['name']:
        raise ValueError('ZIP filename mismatch')
    compressed = read(entry['offset'] + 30 + name_size + extra_size, entry['compressed'])
    if entry['method'] == 8:
        decoder = zlib.decompressobj(-15)
        body = decoder.decompress(compressed, entry['size'] + 1)
        if not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:
            raise ValueError('Unexpected compressed member length')
    else:
        body = compressed
    validate_source(body, entry)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
        temporary.write(body)
        pending = Path(temporary.name)
    if destination.exists():
        pending.unlink()
        raise FileExistsError(destination)
    pending.rename(destination)


def read_rows(path, key):
    result = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        identity = str(row[key])
        if identity in result:
            raise ValueError('Duplicate metadata ID: ' + identity)
        result[identity] = row
    return result


def numeric(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_catalog(source):
    master = read_rows(source / 'static/mst_decoded/F_UNIT_MST.ndjson', '3HriTp6B')
    names = read_rows(source / 'static/text_decoded/F_TEXT_UNITS_NAME.ndjson', 'key')
    recipes = read_rows(source / 'static/mst_decoded/F_UNIT_CLASS_UP_MST.ndjson', '3HriTp6B')

    def maximum(uid):
        visited = set()
        while uid in recipes:
            if uid in visited:
                return None
            visited.add(uid)
            target = str(recipes[uid].get('t74crqAL', ''))
            if target in ('', '0', 'null'):
                break
            if target not in master:
                return None
            uid = target
        return numeric(master[uid].get('9fW0TePj'))

    units = {}
    for uid, row in sorted(master.items()):
        if not uid.isdigit():
            raise ValueError('Unexpected master ID')
        value = names.get('MST_UNIT_NAME_' + uid, {}).get('v')
        name = value[0] if isinstance(value, list) and value and isinstance(value[0], str) else None
        root = str(row.get('woghJa61', ''))
        base = master.get(root)
        base_rarity = numeric(base.get('9fW0TePj')) if base and str(base.get('woghJa61')) == root else None
        units[uid] = {'name': name, 'rarity_code': numeric(row.get('9fW0TePj')),
                      'series_root': root if base else None, 'base_rarity_code': base_rarity,
                      'max_awakening_rarity_code': maximum(uid), 'artwork': None}
    return {'schema': 1, 'mode': 'preservation', 'units': units}


def validate_png(body):
    return png_info(body)


def verify_bundle(root):
    root = Path(root)
    lock = load_lock()
    receipt = json.loads((root / 'receipt.json').read_text())
    if receipt['source_lock_sha256'] != sha(LOCK.read_bytes()):
        raise ValueError('Content was imported with a different lock; use a new output directory')
    expected_files = {'catalog.json'} | {'sprites/' + r['unit_id'] + '.png' for r in lock['artwork']}
    if set(receipt['files']) != expected_files:
        raise ValueError('Unexpected bundled files')
    for relative, digest in receipt['files'].items():
        if sha((root / relative).read_bytes()) != digest:
            raise ValueError('Imported file checksum mismatch: ' + relative)
    for row in lock['artwork']:
        body = (root / 'sprites' / (row['unit_id'] + '.png')).read_bytes()
        if sha(body) != row['sha256']:
            raise ValueError('Artwork differs from pinned source: ' + row['unit_id'])
        validate_png(body)
    return receipt


def import_content(source=DEFAULT_SOURCE, output=None, download=False, client=None):
    source, output = Path(source), Path(output or default_output())
    lock = load_lock()
    for entry in lock['members']:
        path = source / entry['name']
        if not path.exists() and download:
            download_member(entry, path, client)
        if not path.exists():
            raise FileNotFoundError('Missing pinned input: %s. Run import_content.py --download, or pass --source-cache.' % path)
        validate_source(path.read_bytes(), entry)
    catalog = build_catalog(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='unit-import-', dir=output.parent) as temporary:
        stage = Path(temporary) / 'UnitContent'
        (stage / 'sprites').mkdir(parents=True)
        indexes = {}
        for art in lock['artwork']:
            if art['file'] != 'unit_ills_' + art['unit_id'] + '.png' or art['unit_id'] not in catalog['units']:
                raise ValueError('Unverified master-ID artwork mapping')
            if 'range_source' in art:
                path = PNG_CACHE / (art['sha256'] + '.png')
                if not path.exists():
                    raise FileNotFoundError('Missing pinned PNG; run import_content.py --download: ' + str(path))
                body = path.read_bytes()
            else:
                path = source / art['cpk_member']
                if path not in indexes:
                    indexes[path] = index(path)
                entry = next(e for e in indexes[path]['entries'] if e['name'] == art['file'])
                if entry['size'] != entry['unpacked']:
                    raise ValueError('Static PNG requires unsupported decompression')
                body = path.read_bytes()[entry['offset']:entry['offset'] + entry['size']]
            if sha(body) != art['sha256']:
                raise ValueError('Extracted sprite checksum mismatch')
            validate_png(body)
            relative = 'sprites/' + art['unit_id'] + '.png'
            (stage / relative).write_bytes(body)
            catalog['units'][art['unit_id']]['artwork'] = relative
        encoded = json.dumps(catalog, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        (stage / 'catalog.json').write_bytes(encoded)
        files = {str(p.relative_to(stage)): sha(p.read_bytes()) for p in stage.rglob('*') if p.is_file()}
        receipt = {'schema': 1, 'source_lock_sha256': sha(LOCK.read_bytes()), 'files': files,
                   'master_ids': len(catalog['units']), 'named_ids': sum(bool(u['name']) for u in catalog['units'].values()),
                   'artwork_ids': len(lock['artwork']), 'provenance': lock['origin'], 'sources': lock['members']}
        (stage / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        if output.exists():
            verify_bundle(output)
            if (output / 'catalog.json').read_bytes() != encoded:
                raise FileExistsError('Refusing to replace different imported content: ' + str(output))
        else:
            stage.rename(output)
    return verify_bundle(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-cache', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--download', action='store_true', help='Fetch only missing pinned metadata/CPK/PNG ranges')
    args = parser.parse_args()
    client = None
    if args.download:
        from range_client import RangeClient
        client = RangeClient()
        if load_lock().get('range_sources'):
            from batch_artwork import fetch_locked_images
            fetch_locked_images(load_lock(), client, PNG_CACHE)
    result = import_content(args.source_cache, args.output, args.download, client)
    print(json.dumps({k: result[k] for k in ('master_ids', 'named_ids', 'artwork_ids')}, indent=2))
    print('Validated content:', args.output or default_output())


if __name__ == '__main__':
    main()

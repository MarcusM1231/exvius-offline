"""Build-time import of pinned metadata and three static PNGs. Never opens saves."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib

sys.dont_write_bytecode = True
from cpk_reader import index

IOS = Path(__file__).resolve().parents[1]
LOCK = Path(__file__).with_name('content.lock.json')
DEFAULT_SOURCE = IOS / '.local/unit-content/sources'
DEFAULT_OUTPUT = IOS / '.local/unit-content/UnitContent'


def sha(body):
    return hashlib.sha256(body).hexdigest()


def load_lock():
    return json.loads(LOCK.read_text(encoding='utf-8'))


def validate_source(body, entry):
    if len(body) != entry['size'] or sha(body) != entry['sha256'] or zlib.crc32(body) != entry['crc32']:
        raise ValueError('Pinned source checksum mismatch: ' + entry['name'])


def download_member(entry, destination):
    """Only bounded byte ranges. Abort if the server ignores Range; no full ZIP fallback."""
    def read(offset, length):
        if length > 1024 * 1024 or offset < 0 or offset + length > entry['archive_size']:
            raise ValueError('Refusing unexpected archive range')
        with tempfile.TemporaryDirectory() as temp:
            headers = Path(temp) / 'headers'
            result = subprocess.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location',
                '--max-time', '60', '--max-filesize', str(1024 * 1024), '--range',
                '%s-%s' % (offset, offset + length - 1), '--dump-header', str(headers), entry['url'] + '?phase5b-range=' + str(time.time_ns())],
                capture_output=True, timeout=70)
            if result.returncode:
                raise RuntimeError(result.stderr.decode(errors='replace'))
            import re
            ranges = re.findall(r'content-range:\s*([^\r\n]+)', headers.read_text(), re.I)
            expected = 'bytes %s-%s/%s' % (offset, offset + length - 1, entry['archive_size'])
            if not ranges or ranges[-1] != expected or len(result.stdout) != length:
                raise ValueError('Server did not return the exact requested range')
            return result.stdout
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
    # A fresh temporary file is renamed only after validation. Never replace another input.
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
    if not body.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Expected original PNG')
    position = 8
    saw_end = False
    while position < len(body):
        size = struct.unpack_from('>I', body, position)[0]
        chunk = body[position + 4:position + 8 + size]
        expected = struct.unpack_from('>I', body, position + 8 + size)[0]
        if zlib.crc32(chunk) != expected:
            raise ValueError('PNG chunk checksum mismatch')
        position += size + 12
        if chunk[:4] == b'IEND':
            saw_end = True
            break
    if not saw_end or position != len(body):
        raise ValueError('Incomplete PNG')


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


def import_content(source=DEFAULT_SOURCE, output=DEFAULT_OUTPUT, download=False):
    source, output = Path(source), Path(output)
    lock = load_lock()
    for entry in lock['members']:
        path = source / entry['name']
        if not path.exists() and download:
            download_member(entry, path)
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
            path = source / art['cpk_member']
            if path not in indexes:
                indexes[path] = index(path)
            entry = next(e for e in indexes[path]['entries'] if e['name'] == art['file'])
            if art['file'] != 'unit_ills_' + art['unit_id'] + '.png' or art['unit_id'] not in catalog['units']:
                raise ValueError('Unverified master-ID artwork mapping')
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
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--download', action='store_true', help='Fetch only five pinned ZIP members if missing')
    args = parser.parse_args()
    result = import_content(args.source_cache, args.output, args.download)
    print(json.dumps({k: result[k] for k in ('master_ids', 'named_ids', 'artwork_ids')}, indent=2))
    print('Validated content:', args.output)


if __name__ == '__main__':
    main()

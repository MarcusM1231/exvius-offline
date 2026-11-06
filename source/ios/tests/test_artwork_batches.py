"""Batch publication, corruption/duplicates, transparent PNGs, and bounded network behavior."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.dont_write_bytecode = True
IOS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IOS/'content_tools'))
from png_validation import png_info
from range_client import RangeClient, RangeError
from batch_artwork import coalesce, cache_image, validate_artwork, publish_batch, fetch_locked_images
from import_content import LOCK, PNG_CACHE, default_output, load_lock, verify_bundle, build_catalog, DEFAULT_SOURCE, download_member


def chunk(kind, data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))


def rgba(alpha=0):
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(bytes([0,10,20,30,alpha])))+chunk(b'IEND',b'')


class BatchTests(unittest.TestCase):
    def test_png_crc_alpha_and_actual_transparent_pixels(self):
        self.assertEqual(png_info(rgba())['transparent_pixels'],1)
        with self.assertRaisesRegex(ValueError,'no actual transparent'):
            png_info(rgba(255))
        broken=bytearray(rgba());broken[-5]^=1
        with self.assertRaises(ValueError):png_info(bytes(broken))
        with self.assertRaises(ValueError):png_info(rgba()[:-4])

    def test_unused_transparent_palette_entry_is_not_accepted(self):
        header=chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,3,0,0,0))
        palette=chunk(b'PLTE',bytes([255,0,0,0,0,0]))+chunk(b'tRNS',bytes([255,0]))
        body=b'\x89PNG\r\n\x1a\n'+header+palette+chunk(b'IDAT',zlib.compress(bytes([0,0])))+chunk(b'IEND',b'')
        with self.assertRaisesRegex(ValueError,'no actual transparent'):png_info(body)

    def test_checksum_identity_and_cache_conflicts(self):
        body=rgba();digest=hashlib.sha256(body).hexdigest()
        row={'unit_id':'123','file':'unit_ills_123.png','size':len(body),'sha256':digest}
        self.assertEqual(validate_artwork(row,body)['width'],1)
        with self.assertRaisesRegex(ValueError,'filename'):
            validate_artwork(dict(row,file='unit_ills_124.png'),body)
        with self.assertRaisesRegex(ValueError,'checksum'):
            validate_artwork(row,rgba(1))
        with tempfile.TemporaryDirectory() as temp:
            cache_image(temp,digest,body)
            cache_image(temp,digest,body)
            with self.assertRaisesRegex(ValueError,'cache checksum'):
                cache_image(temp,digest,b'bad')

    def test_coalescing_is_bounded_and_rejects_overlapping_ranges(self):
        rows=[{'offset':0,'size':10},{'offset':20,'size':10},{'offset':1000,'size':20}]
        groups=coalesce(rows,max_gap=10,max_read=100)
        self.assertEqual([(a,b) for a,b,_ in groups],[(0,30),(1000,1020)])
        with self.assertRaisesRegex(ValueError,'Overlapping'):
            coalesce([{'offset':0,'size':20},{'offset':10,'size':20}])
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            coalesce([{'offset':0,'size':200000}])

    def test_network_error_and_ignored_range_stop_without_retry(self):
        source={'archive':'test','archive_size':1000,'url':'https://github.com/example/file'}
        for status,headers in [('429','HTTP/2 429\r\nRetry-After: 90\r\n'),('200','HTTP/2 200\r\n')]:
            calls=[]
            def fake(args,**kwargs):
                calls.append(args)
                Path(args[args.index('--dump-header')+1]).write_text(headers)
                Path(args[args.index('--output')+1]).write_bytes(b'1234')
                class Result:returncode=0;stdout=(status+'\nhttps://github.com/example/file').encode();stderr=b''
                return Result()
            with patch('range_client.subprocess.run',side_effect=fake):
                with self.assertRaises(RangeError):RangeClient().read(source,0,4)
            self.assertEqual(len(calls),1)
        with self.assertRaises(RangeError):RangeClient().read(source,0,2*1024*1024)

    def test_pinned_member_download_validates_ranges_and_identity(self):
        body=b'pinned metadata fixture'
        encoded=zlib.compress(body)[2:-4]
        name=b'static/example.ndjson'
        header=bytearray(30);header[:4]=b'PK\x03\x04'
        struct.pack_into('<HH',header,26,len(name),0)
        archive=bytes(header)+name+encoded
        entry={'offset':0,'name':name.decode(),'compressed':len(encoded),'method':8,
               'size':len(body),'sha256':hashlib.sha256(body).hexdigest(),'crc32':zlib.crc32(body)}
        calls=[]
        class MemoryRanges:
            def read(self,source,offset,length):
                calls.append((offset,length))
                return archive[offset:offset+length]
        with tempfile.TemporaryDirectory() as temp:
            destination=Path(temp)/'member'
            download_member(entry,destination,MemoryRanges())
            self.assertEqual(destination.read_bytes(),body)
            self.assertEqual(calls,[(0,30),(30,len(name)),(30+len(name),len(encoded))])
            with self.assertRaisesRegex(ValueError,'checksum'):
                download_member(dict(entry,sha256='0'*64),Path(temp)/'bad',MemoryRanges())
            self.assertFalse((Path(temp)/'bad').exists())

    def test_locked_batch_rebuild_uses_verified_cache_without_network(self):
        lock=load_lock()
        class NoNetwork:
            def read(self,*args):raise AssertionError('Unexpected network')
        fetch_locked_images(lock,NoNetwork())
        receipt=verify_bundle(default_output())
        self.assertEqual(receipt['artwork_ids'],len(lock['artwork']))
        for row in lock['artwork']:
            if 'range_source' in row:
                self.assertGreater(png_info((PNG_CACHE/(row['sha256']+'.png')).read_bytes())['transparent_pixels'],0)

    def test_duplicate_and_conflicting_ids_cannot_change_lock(self):
        before=LOCK.read_bytes();row=load_lock()['artwork'][0]
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            publish_batch([row,row],{}, {})
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            publish_batch([dict(row,sha256='0'*64)],{}, {})
        self.assertEqual(LOCK.read_bytes(),before)

    def test_failed_bundle_publication_rolls_back_lock(self):
        before=LOCK.read_bytes()
        with patch('batch_artwork.import_content',side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):publish_batch([],{},dict(load_lock().get('targets',{}), test_marker='must-roll-back'))
        self.assertEqual(LOCK.read_bytes(),before)
        verify_bundle(default_output())

    def test_coverage_and_metadata_remain_consistent(self):
        lock=load_lock();target=lock['targets'];have={r['unit_id'] for r in lock['artwork']}
        self.assertTrue(have <= set(target['demo_ids']))
        self.assertEqual(len(have),len(lock['artwork']))
        baseline=IOS/'.local/unit-content/UnitContent/catalog.json'
        current=json.loads((default_output()/'catalog.json').read_text())
        old=json.loads(baseline.read_text()) if baseline.exists() else build_catalog(DEFAULT_SOURCE)
        for uid,row in old['units'].items():
            self.assertEqual({k:v for k,v in row.items() if k!='artwork'},
                             {k:v for k,v in current['units'][uid].items() if k!='artwork'})
        self.assertTrue(have >= {'100004203','100000102','100000202'})


if __name__=='__main__':unittest.main(verbosity=2)

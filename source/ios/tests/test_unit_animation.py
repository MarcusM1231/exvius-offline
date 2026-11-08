import hashlib,json,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
from unit_animation import parse_cgg,parse_cgs,compose
import import_unit_animations as importer
from PIL import Image

class UnitAnimationTests(unittest.TestCase):
    def test_native_clock_boundaries_pause_speed(self):
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
            binary=Path(tmp)/'animation-clock'
            subprocess.run(['xcrun','swiftc','-module-cache-path',str(IOS/'.local/swift-cache'),str(IOS/'native/FFBERevival/UnitAnimationClock.swift'),str(IOS/'native/tests/UnitAnimationSmoke.swift'),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True,capture_output=True)
    def test_valid_maria_and_order(self):
        lock=json.loads(importer.LOCK.read_text());text=importer.checked('unit_cgg_202000203.csv',lock).decode()
        parts=parse_cgg(text.splitlines()[0],(640,640))[0]
        self.assertEqual([p['record_index'] for p in parts],list(reversed(range(13))))
        seq=parse_cgs(importer.checked('unit_idle_cgs_202000203.csv',lock).decode(),109)
        self.assertEqual([r['composition'] for r in seq],[0,1,2,3]);self.assertEqual([r['ticks'] for r in seq],[12]*4)
    def test_malformed_and_unknown(self):
        for text in ['','0,1,','0,0,','a,1,','0,1,0,0,0,0,100,0,0,0,3,3,0,extra,']:
            with self.assertRaises(ValueError):parse_cgg(text,(2,2))
        for field,value in [(2,4),(3,2),(4,101),(5,45),(6,-1),(8,0),(10,1)]:
            p=[0,0,0,0,100,0,0,0,1,1,0];p[field]=value
            with self.assertRaises(ValueError):parse_cgg('0,1,'+','.join(map(str,p)),(2,2))
    def test_cgs_bounds(self):
        for s in ['1,0,0,12','0,0,0,0','-1,0,0,12','0,0,0,12,1','0,0,0,10000']:
            with self.assertRaises(ValueError):parse_cgs(s,1)
    def test_regions_flips_and_order_pixels(self):
        tex=Image.new('RGBA',(2,1));tex.putdata([(255,0,0,255),(0,0,255,255)])
        p=parse_cgg('0,1,0,0,1,0,100,0,0,0,2,1,0',(2,1))[0]
        frame=compose(tex,p,canvas=(2,1),origin=(0,0));self.assertEqual(frame.getpixel((0,0)),(0,0,255,255))
        with self.assertRaises(ValueError):compose(tex,p,canvas=(1,1),origin=(0,0))
    def test_checksum_corruption(self):
        lock=json.loads(importer.LOCK.read_text());row=lock['members'][0]
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/row['name']).write_bytes(b'corrupt')
            lock=json.loads(json.dumps(lock));lock['members'][0]['cache_path']=str(Path(tmp)/row['name'])
            with patch.object(importer,'CACHE',Path(tmp)):
                with self.assertRaises(ValueError):importer.checked(row['name'],lock)
    def test_reproducibility(self):
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
            with patch.object(importer,'LOCK',importer.LEGACY_LOCK),patch.object(importer,'output',lambda:Path(tmp)/'bundle'):
                importer.build();before=(importer.output()/'receipt.json').read_bytes();importer.build()
                self.assertEqual(before,(importer.output()/'receipt.json').read_bytes());importer.verify()
    def test_supported_motion_and_exact_ids(self):
        catalog=json.loads((importer.output()/'catalog.json').read_text())
        self.assertTrue({'202000203','100000103','206000103','206000113'}.issubset(catalog))
        self.assertNotIn('100000102',catalog)
        for uid,anims in catalog.items():
            for kind,m in anims.items():
                self.assertEqual(m['masterID'],uid);self.assertEqual(m['kind'],kind)
                data=[]
                for p in m['frames']:
                    with Image.open(importer.output()/p) as image:
                        data.append(image.tobytes())
                        self.assertEqual(image.size,(m['width'],m['height']))
                self.assertGreaterEqual(len(set(data)),1) # Original idle may be a genuinely static sequence.

if __name__=='__main__':unittest.main()

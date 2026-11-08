import json,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
from unit_animation import staging_bounds,compose,parse_cgg,parse_cgs
from import_content import sha
import import_unit_attacks as attacks
import import_unit_animations as importer
from PIL import Image
class AttackTests(unittest.TestCase):
    def test_dynamic_bounds_preserve_pixels_and_offsets(self):
        parts=parse_cgg('0,1,-744,-157,0,0,100,0,0,0,2,1,0',(2,1))[0]
        seq=[dict(composition=0,offset_x=0,offset_y=0,ticks=10)]
        b=staging_bounds({0:parts},seq);self.assertEqual(b,(-744,-157,-742,-156))
        tex=Image.new('RGBA',(2,1),(255,0,0,255));im=compose(tex,parts,canvas=(2,1),origin=(744,157))
        self.assertEqual(im.getpixel((0,0)),(255,0,0,255))
        with self.assertRaises(ValueError):compose(tex,parts)
    def test_attack_budget_rejects_unbounded(self):
        p=dict(x=-2048,y=0,width=4096,height=1,rotation=0)
        with self.assertRaises(ValueError):staging_bounds({0:[p]},[dict(composition=0,offset_x=0,offset_y=0)])
    def test_finite_policy(self):
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
            binary=Path(tmp)/'policy'
            subprocess.run(['xcrun','swiftc','-module-cache-path',str(IOS/'.local/swift-cache'),str(IOS/'native/FFBERevival/UnitActionSequence.swift'),str(IOS/'native/tests/ObtainedActionSmoke.swift'),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True,capture_output=True)
    def test_completed_recovery_resumes_without_network(self):
        import recover_unit_attacks as r
        class NoNetwork:
            transferred=0
            def read(self,*args):raise AssertionError('Unexpected network')
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
            lock=Path(tmp)/'lock.json';lock.write_bytes(attacks.LOCK.read_bytes());before=lock.read_bytes()
            with patch.object(r,'LOCK',lock),patch.object(r,'ROOT',Path(tmp)),patch.object(r,'RangeClient',return_value=NoNetwork()):
                self.assertEqual(r.recover(),[]);self.assertEqual(before,lock.read_bytes())
    def test_bundle_sources_idle_compatibility_and_coverage(self):
        attacks.verify();old=json.loads((importer.output()/'catalog.json').read_text());new=json.loads((attacks.output()/'catalog.json').read_text())
        lock=json.loads(attacks.LOCK.read_text());self.assertEqual(len(set(r['name'] for r in lock['members'])),len(lock['members']))
        for row in lock['members']:self.assertEqual(len(importer.checked(row['name'],lock)),row['unpacked'])
        for uid,clips in old.items():
            for kind,m in clips.items():
                self.assertEqual(new[uid][kind],m)
                for name in m['frames']:self.assertEqual((importer.output()/name).read_bytes(),(attacks.output()/name).read_bytes())
        self.assertIn('atk',new['205000703']);self.assertIn('atk',new['206000113']);self.assertIn('atk',new['100005404'])
        coverage=json.loads((attacks.output()/'coverage.json').read_text());self.assertEqual(sum(r['is_target'] for r in coverage.values()),423)
    def test_selected_batch_reproducibility(self):
        lock=json.loads(attacks.LOCK.read_text());ids={'100005404','206000113'}
        lock['members']=[r for r in lock['members'] if r['unit_id'] in ids]
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
            root=Path(tmp);p=root/'lock.json';p.write_text(json.dumps(lock,sort_keys=True))
            for name in ['one','two']:
                importer.build(lock_path=p,destination=root/name,kinds=['idle','atk'],research_root=root/'previews',report_path=root/'report.json',dynamic_attacks=True)
            self.assertEqual((root/'one/receipt.json').read_bytes(),(root/'two/receipt.json').read_bytes())
            frame=next((root/'one').rglob('*.png'));frame.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):importer.verify(root=root/'one',lock_path=p)
    def test_original_member_index_identity(self):
        lock=json.loads(attacks.LOCK.read_text())
        indexes={}
        for key,source in lock['sources'].items():
            raw=(IOS/source['index_path']).read_bytes();self.assertEqual(sha(raw),source['index_sha256'])
            indexes[key]={r['name']:r for r in json.loads(raw)['entries']}
        for row in lock['members']:
            member=indexes[row['source']][row['name']]
            for field in ['offset_in_cpk','size','unpacked']:self.assertEqual(row[field],member[field])
    def test_source_ticks_and_bounds(self):
        lock=json.loads(attacks.LOCK.read_text());catalog=json.loads((attacks.output()/'catalog.json').read_text())
        for uid,clips in catalog.items():
            if 'atk' not in clips:continue
            m=clips['atk'];seq=parse_cgs(importer.checked(f'unit_atk_cgs_{uid}.csv',lock).decode(),4096)
            self.assertEqual(m['ticks'],[r['ticks'] for r in seq]);self.assertLessEqual(m['width']*m['height']*len(m['frames'])*4,33554432)
        self.assertEqual(sum(catalog['100005404']['atk']['ticks']),107)
if __name__=='__main__':unittest.main()

import json,sys,subprocess,tempfile,unittest
from pathlib import Path
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import import_unit_action_research as actions
import import_unit_animations as importer
from import_content import sha
from unit_animation import parse_cgs

class ActionTests(unittest.TestCase):
    def test_action_sources_and_original_idle_pin(self):
        lock=json.loads(actions.LOCK.read_text());base=json.loads(importer.EXPANDED_LOCK.read_text());old={r['name']:r for r in base['members']}
        self.assertEqual(lock['base_lock_sha256'],sha(importer.EXPANDED_LOCK.read_bytes()))
        for row in lock['members']:
            self.assertEqual(len(importer.checked(row['name'],lock)),row['unpacked'])
            if row['name'] in old:self.assertEqual(row['sha256_stored'],old[row['name']]['sha256_stored'])
        actions.verify();importer.verify()
    def test_six_units_and_supported_actions(self):
        root=actions.output();catalog=json.loads((root/'catalog.json').read_text());support=json.loads((root/'support.json').read_text())
        self.assertEqual(set(catalog),{'202000203','100000103','206000103','206000113','100004604','205000703'})
        for uid in catalog:
            for name in ['idle','standby','magic_atk','win_before','win']:self.assertIn(name,catalog[uid])
            for kind,m in catalog[uid].items():
                self.assertEqual(m['kind'],kind);self.assertEqual(m['masterID'],uid);self.assertTrue(all(t>0 for t in m['ticks']))
                self.assertLessEqual(len(m['frames']),64);self.assertLessEqual(m['width']*m['height']*len(m['frames'])*4,8388608)
        self.assertIn('atk',catalog['100004604']);self.assertIn('atk',catalog['202000203'])
        self.assertIn('Composition canvas bounds',support['206000113']['unsupported']['atk'])
    def test_zero_duration_is_not_invented_loop_marker(self):
        with self.assertRaises(ValueError):parse_cgs('0,0,0,0,',1)
    def test_native_sequence_and_clock(self):
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as tmp:
            binary=Path(tmp)/'actions'
            subprocess.run(['xcrun','swiftc','-module-cache-path',str(IOS/'.local/swift-cache'),str(IOS/'native/FFBERevival/UnitAnimationClock.swift'),str(IOS/'native/FFBERevival/UnitActionSequence.swift'),str(IOS/'native/tests/UnitActionSequenceSmoke.swift'),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True,capture_output=True)
    def test_gameplay_crystal_and_idle_locks_unchanged_from_checkpoint(self):
        for relative in ['native/FFBERevival/CrystalReconstruction.swift','native/FFBERevival/CharacterRevealState.swift','prototype/summon_service.py','content_tools/unit-animation-expanded.lock.json']:
            committed=subprocess.check_output(['git','show','d0d1103:source/ios/'+relative],cwd=IOS)
            self.assertEqual((IOS/relative).read_bytes(),committed,relative)
    def test_menu_preserves_committed_reveal_helpers(self):
        relative='native/FFBERevival/SummonInterface.swift'
        committed=subprocess.check_output(['git','show','6da00ff:source/ios/'+relative],cwd=IOS).decode()
        current=(IOS/relative).read_text()
        def helpers(text):return text[text.index('    private func presentCommittedIfReady()'):text.index('    private var lapis:')]
        self.assertEqual(helpers(current),helpers(committed))
    def test_research_has_no_campaign_or_reward_api(self):
        text=(IOS/'native/FFBERevival/UnitActionResearch.swift').read_text()
        for prohibited in ['EmbeddedSummonBackend','PythonWorker','SummonModel','URLSession','roll_gacha','campaign.json']:
            self.assertNotIn(prohibited,text)
if __name__=='__main__':unittest.main()

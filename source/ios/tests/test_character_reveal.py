"""Production reveal import/state contracts; existing gameplay is tested separately."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
IOS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(IOS/'content_tools'))
import import_character_reveal as content

class CharacterRevealTests(unittest.TestCase):
    def test_native_deterministic_sequence_and_safety(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'reveal'
            subprocess.run(['xcrun','swiftc','-module-cache-path',str(IOS/'.local/swift-cache'),str(IOS/'native/FFBERevival/API.swift'),str(IOS/'native/FFBERevival/CharacterRevealState.swift'),str(IOS/'native/tests/CharacterRevealSmoke.swift'),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True)
    def test_pinned_cells_import_without_network_or_research_changes(self):
        research=IOS/'content_tools/reveal-research.lock.json';before=research.read_bytes()
        with tempfile.TemporaryDirectory() as tmp,patch('socket.socket',side_effect=AssertionError('network forbidden')):
            a=content.run(Path(tmp));self.assertEqual(a,content.run(Path(tmp)))
            self.assertIn('get.png',a['files']);self.assertIn('star_3.png',a['files']);self.assertNotIn('neovision_plus_glow.png',a['files'])
        self.assertEqual(before,research.read_bytes())
    def test_changed_production_asset_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);content.run(p);(p/'get.png').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'checksum'):content.verify(p)
    def test_runtime_manifest_pin_matches_import_lock(self):
        import hashlib
        source=(IOS/'native/FFBERevival/SummonCharacterReveal.swift').read_text()
        self.assertIn(hashlib.sha256(content.LOCK.read_bytes()).hexdigest(),source)
    def test_reveal_has_no_reward_or_save_api_and_grid_is_preserved(self):
        source=(IOS/'native/FFBERevival/SummonCharacterReveal.swift').read_text()
        for banned in ['PythonWorker','SummonModel','EmbeddedSummonBackend','URLSession','campaign.json','roll_gacha']:
            self.assertNotIn(banned,source)
        interface=(IOS/'native/FFBERevival/SummonInterface.swift').read_text()
        self.assertIn('CommittedSummonPresentation(receipt: receipt)',interface)
        self.assertIn('presentedAwards = receipt.awards',interface)
        self.assertIn('struct GlobalSummonResults',interface)

if __name__=='__main__':unittest.main()

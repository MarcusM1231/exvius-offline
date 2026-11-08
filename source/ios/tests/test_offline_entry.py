"""Packaged subset, no site-packages, fresh interpreter, real summon transactions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
IOS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IOS / 'native/scripts'))
from package_python import package_code


class OfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch = IOS / '.local'
        scratch.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='offline-tests-', dir=scratch)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name).resolve()
        cls.bundle = cls.root / 'PythonApp'
        package_code(cls.bundle)

    def run_code(self, code, save_name=None):
        storage = self.root / (save_name or self._testMethodName)
        setup = f'''
import json,sys
from pathlib import Path
sys.path.insert(0, {str(self.bundle / 'source/ios/embedded')!r})
import offline_entry as entry
storage = Path({str(storage)!r})
data = Path({str(self.bundle / 'metadata/demo')!r})
def call(operation, **args):
    return json.loads(entry.dispatch(json.dumps(dict(operation=operation, **args))))
def initialize():
    result = call('initialize', data=str(data), storage=str(storage))
    assert result['ok'], result
'''
        result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', setup + '\n' + code],
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_explicit_developer_lapis_grant(self):
        self.run_code("""
initialize()
before = call('state')['value']
for invalid in ('0','-1','100001','1.5','abc'):
    assert not call('developer_add_lapis', amount=invalid)['ok']
assert call('state')['value'] == before
result = call('developer_add_lapis', amount='10000')
assert result['ok'], result
after = result['value']
assert after['currencies']['lapis_free'] == before['currencies']['lapis_free'] + 10000
assert after['units'] == before['units'] and after['last_pull'] == before['last_pull']
assert json.loads((storage/'campaign.json').read_text())['currencies']['lapis_free'] == after['currencies']['lapis_free']
original = entry._service._save
def fail(): raise OSError('injected failure')
entry._service._save = fail
assert not call('developer_add_lapis', amount='10')['ok']
assert call('state')['value'] == after
entry._service._save = original
""")

    def test_hello_and_single_real_summon(self):
        self.run_code('''
proof = call('hello')['value']
assert proof['answer'] == 42
initialize()
catalogue = call('banners')['value']['banners']
banner = next(b for b in catalogue if b['id'] == '9100203')
assert [o['cost']['amount'] for o in banner['offer_details']] == [500,5000]
before = call('state')['value']
result = call('summon', banner_id='9100203')
assert result['ok'], result
assert result['value']['state']['currencies']['lapis_free'] == 9500
assert len(result['value']['state']['units']) == len(before['units']) + 1
assert all('name' in u for u in call('state')['value']['units'])
assert not any(m in sys.modules for m in ('cryptography','yaml','capture_server','summon_api'))
''')

    def test_fresh_interpreter_reload(self):
        self.run_code("initialize(); assert call('summon', banner_id='49', offer='secondary')['ok']")
        self.run_code('''
initialize()
s = call('state')['value']
assert s['currencies']['lapis_free'] == 5000
assert len(s['units']) == 13
assert len(s['last_pull']['awards']) == 11
assert any(int(a['granted_rarity']) >= 4 for a in s['last_pull']['awards'])
''')

    def test_refusal_and_failed_save_rollback(self):
        self.run_code('''
initialize()
assert call('summon', banner_id='9100203', offer='secondary')['ok']
assert call('summon', banner_id='9100203', offer='secondary')['ok']
before = call('state')['value']
saved = (storage / 'campaign.json').read_bytes()
refused = call('summon', banner_id='9100203')
assert refused['error']['code'] == 'summon_refused'
assert call('state')['value'] == before
assert (storage / 'campaign.json').read_bytes() == saved
entry._service.player.add_currency('lapis_free', 500)
before = call('state')['value']
entry._service.player.save = lambda path: False
failed = call('summon', banner_id='9100203')
assert failed['error']['code'] == 'save_failed'
assert call('state')['value'] == before
assert (storage / 'campaign.json').read_bytes() == saved
''')

    def test_network_and_processes_denied(self):
        self.run_code('''
initialize()
import socket,subprocess
for action in (lambda: socket.socket(), lambda: socket.getaddrinfo('example.com',80),
               lambda: subprocess.run(['echo','unexpected'])):
    try: action()
    except RuntimeError: pass
    else: raise AssertionError('Offline guard did not reject external operation')
assert call('summon', banner_id='9100203')['ok']
''')

    def test_corrupt_save_is_preserved(self):
        self.run_code('''
storage.mkdir(parents=True)
save = storage / 'campaign.json'
save.write_text('{broken')
result = call('initialize', data=str(data), storage=str(storage))
assert not result['ok']
assert save.read_text() == '{broken'
''')

    def test_bundle_unchanged_and_validation(self):
        def hashes():
            return {str(p.relative_to(self.bundle)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.bundle.rglob('*') if p.is_file()}
        before = hashes()
        self.run_code('''
initialize()
for request in ('[]', '{}', '{"operation":"summon","banner_id":5}',
                '{"operation":"summon","banner_id":"49","offer":"bad"}'):
    assert not json.loads(entry.dispatch(request))['ok']
assert call('summon', banner_id='missing')['error']['code'] == 'unknown_banner'
assert call('summon', banner_id='9100203')['ok']
assert call('initialize', data=str(data), storage=str(data))['ok'] is False
''')
        self.assertEqual(hashes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)

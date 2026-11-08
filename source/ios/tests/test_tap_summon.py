"""Tap gate, exactly-once frontend, real post-commit response loss and cold recovery."""
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
sys.dont_write_bytecode=True
IOS=Path(__file__).resolve().parents[1]

class TapSummonTests(unittest.TestCase):
    def compile(self, name, destination):
        sources=['API.swift','CrystalPlayback.swift','TapSummonState.swift','CrystalEntrance.swift']
        subprocess.run(['xcrun','swiftc','-module-cache-path',str(IOS/'.local/swift-cache'),
                        *[str(IOS/'native/FFBERevival'/n) for n in sources],
                        str(IOS/'native/tests'/name),'-o',str(destination)],check=True,capture_output=True)

    def test_deterministic_state_machine_and_frontend_transaction_contract(self):
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as temp:
            binary=Path(temp)/'contract';self.compile('TapSummonSmoke.swift',binary)
            subprocess.run([str(binary)],check=True)

    def test_real_python_transactions_and_post_commit_response_loss(self):
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as temp:
            root=Path(temp);binary=root/'real';self.compile('TapRealBackendSmoke.swift',binary)
            script='''
import sys,threading,subprocess
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from demo_data import prepare
from summon_service import SummonService
from summon_api import make_server
root=Path(sys.argv[2]);service=SummonService(prepare(root/'data'),root/'isolated.json',demo=True,initial_lapis=10000)
initial_units=len(service.state()['units'])
original=service.summon;roll=service.player.roll_gacha;calls=[];rolls=[]
def counted_roll(*args,**kwargs):
    rolls.append(1);return roll(*args,**kwargs)
service.player.roll_gacha=counted_roll
def response_loss(*args,**kwargs):
    calls.append(1);result=original(*args,**kwargs)
    if len(calls)==3:raise OSError('Injected response failure after durable commit')
    return result
service.summon=response_loss
with make_server(service,port=0) as server:
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:subprocess.run([sys.argv[3],'http://127.0.0.1:%d'%server.server_address[1]],check=True)
    finally:server.shutdown();thread.join()
assert len(calls)==len(rolls)==3,(calls,rolls)
assert len(service.state()['units'])==initial_units+13 and service.state()['currencies']['lapis_free']==4000
'''
            subprocess.run([sys.executable,'-B','-c',textwrap.dedent(script),str(IOS/'prototype'),str(root),str(binary)],check=True)

    def test_committed_awards_survive_fresh_process_without_charge(self):
        with tempfile.TemporaryDirectory(dir=IOS/'.local') as temp:
            root=Path(temp)
            create='''
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from demo_data import prepare
from summon_service import SummonService
r=Path(sys.argv[2]);s=SummonService(prepare(r/'data'),r/'isolated.json',demo=True,initial_lapis=10000)
p=s.summon('9100203','secondary')
(r/'expected.json').write_text(json.dumps({'ids':[a['instance_id'] for a in p['result']['awards']],'balance':5000,'sha':hashlib.sha256((r/'isolated.json').read_bytes()).hexdigest()}))
'''
            reload='''
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from summon_service import SummonService
r=Path(sys.argv[2]);expected=json.loads((r/'expected.json').read_text());s=SummonService(r/'data',r/'isolated.json',demo=True)
def forbidden(*args,**kwargs):raise AssertionError('Cold reload must not summon')
s.player.roll_gacha=forbidden
state=s.state();assert [a['instance_id'] for a in state['last_pull']['awards']]==expected['ids']
assert state['currencies']['lapis_free']==expected['balance']
assert hashlib.sha256((r/'isolated.json').read_bytes()).hexdigest()==expected['sha']
print('Fresh-process committed 11-award recovery passed without charge or save write')
'''
            for script in [create,reload]:
                subprocess.run([sys.executable,'-B','-c',textwrap.dedent(script),str(IOS/'prototype'),str(root)],check=True)

if __name__=='__main__':unittest.main(verbosity=2)

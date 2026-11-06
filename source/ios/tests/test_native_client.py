"""macOS Swift URLSession contract check against an isolated real demo backend."""
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

sys.dont_write_bytecode = True
IOS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IOS / 'prototype'))
from demo_data import prepare
from summon_service import SummonService
from summon_api import make_server


def main():
    scratch = IOS / '.local'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='native-contract-', dir=scratch) as temp:
        root = Path(temp)
        binary = root / 'client-smoke'
        subprocess.run(['xcrun', 'swiftc', '-module-cache-path', str(scratch / 'swift-cache'),
            str(IOS / 'native/FFBERevival/API.swift'), str(IOS / 'native/tests/ClientSmoke.swift'),
            '-o', str(binary)], check=True)
        service = SummonService(prepare(root / 'data'), root / 'campaign.json', demo=True, initial_lapis=10000)
        with make_server(service, port=0) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                subprocess.run([str(binary), 'http://127.0.0.1:%s' % server.server_address[1]],
                               check=True, timeout=60)
            finally:
                server.shutdown()
                thread.join()


if __name__ == '__main__':
    main()

"""HTTP contract tests using real backend transactions in an isolated process."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
IOS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IOS / 'prototype'))
from demo_data import prepare
from summon_service import SummonService
from summon_api import make_server, private_address


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch = IOS / '.local'
        scratch.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(dir=scratch)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.data = prepare(cls.root / 'data')

    def setUp(self):
        self.service = SummonService(self.data, self.root / (self._testMethodName + '.json'),
                                     demo=True, initial_lapis=10000)
        self.server = make_server(self.service, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, body=None, content_type='application/json'):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=10)
        try:
            connection.request(method, path, body, {'Content-Type': content_type})
            response = connection.getresponse()
            self.assertEqual(response.getheader('Content-Type'), 'application/json; charset=utf-8')
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def summon(self):
        return self.request('POST', '/v1/summons', json.dumps({'banner_id':'9100203'}))

    def test_full_contract_and_reload(self):
        status, catalogue = self.request('GET', '/v1/banners')
        self.assertEqual(status, 200)
        banner = next(b for b in catalogue['banners'] if b['id'] == '9100203')
        self.assertEqual([o['cost']['amount'] for o in banner['offer_details']], [500, 5000])
        status, response = self.summon()
        self.assertEqual(status, 200)
        self.assertEqual(response['state']['currencies']['lapis_free'], 9500)
        status, units = self.request('GET', '/v1/units')
        self.assertEqual(len(units['units']), 3)
        self.assertTrue(all(u['name'] for u in units['units']))
        status, results = self.request('GET', '/v1/results')
        self.assertEqual(results['last_pull']['awards'], response['state']['last_pull']['awards'])
        restored = SummonService(self.data, self.service.save_path, demo=True)
        self.assertEqual(restored.state(), self.service.state())

    def test_validation_and_errors_preserve_state(self):
        before = self.service.state()
        for body in ('{', '[]', '{}', '{"banner_id":5}',
                     '{"banner_id":"49","offer":"other"}',
                     '{"banner_id":"49","extra":true}'):
            self.assertEqual(self.request('POST', '/v1/summons', body)[0], 400)
        self.assertEqual(self.request('POST', '/v1/summons', '{}', 'text/plain')[0], 415)
        self.assertEqual(self.request('POST', '/v1/summons', 'x'*4097)[0], 413)
        self.assertEqual(self.request('POST', '/v1/summons', '{"banner_id":"missing"}')[0], 404)
        self.assertEqual(self.request('GET', '/missing')[0], 404)
        self.assertEqual(self.request('DELETE', '/v1/summons')[0], 405)
        self.assertEqual(self.service.state(), before)

    def test_concurrent_requests_cannot_overdraw(self):
        with ThreadPoolExecutor(max_workers=6) as workers:
            responses = list(workers.map(lambda _: self.summon(), range(24)))
        self.assertEqual(sum(status == 200 for status, _ in responses), 20)
        self.assertEqual(sum(status == 409 for status, _ in responses), 4)
        state = self.service.state()
        self.assertEqual(state['currencies']['lapis_free'], 0)
        self.assertEqual(len(state['units']), 22)
        self.assertEqual(len({u['instance_id'] for u in state['units']}), 22)

    def test_save_failure_returns_500_and_rolls_back(self):
        before = self.service.state()
        with patch.object(self.service.player, 'save', return_value=False):
            status, body = self.summon()
        self.assertEqual(status, 500)
        self.assertEqual(body['error']['code'], 'save_failed')
        self.assertEqual(self.service.state(), before)

    def test_only_explicit_private_bind_addresses(self):
        for value in ('0.0.0.0', '8.8.8.8', '169.254.1.1', 'example.com'):
            with self.assertRaises((ValueError, argparse.ArgumentTypeError)):
                private_address(value)
        self.assertEqual(private_address('192.168.1.20'), '192.168.1.20')


if __name__ == '__main__':
    unittest.main(verbosity=2)

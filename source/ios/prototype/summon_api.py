"""Private development HTTP adapter; one process/service per campaign."""
import argparse
import ipaddress
import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from summon_service import SummonError
from banner_menu import MenuSummonService as SummonService

MAX_BODY = 4096


def private_address(value):
    address = ipaddress.IPv4Address(value)
    if not (address.is_loopback or any(address in ipaddress.IPv4Network(net)
            for net in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))):
        raise argparse.ArgumentTypeError('Use loopback or an explicit private LAN IPv4 address')
    return str(address)


def make_server(service, host='127.0.0.1', port=8765):
    private_address(host)

    class Handler(BaseHTTPRequestHandler):
        # Close each response; bound slow/incomplete request reads.
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def reply(self, status, payload):
            body = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True
            self.wfile.write(body)

        def error(self, status, code, message):
            self.reply(status, {'error': {'code': code, 'message': message}})

        def do_GET(self):
            try:
                path = urlsplit(self.path).path
                # Hold the facade lock across projections as well as transactions.
                with service.lock:
                    if path == '/v1/banners':
                        banners = service.banners()
                        for banner in banners:
                            banner['offer_details'] = [dict(
                                offer=offer,
                                **{key: value for key, value in service.details(banner['id'], offer).items()
                                   if key in ('cost', 'draws', 'guarantee')})
                                for offer in banner['offers']] if banner['supported'] else []
                        self.reply(200, {'banners': banners})
                    elif path == '/v1/menu':
                        self.reply(200, service.menu()) if hasattr(service, 'menu') else self.error(501, 'menu_unavailable', 'Update the HTTP facade for the banner menu')
                    elif path == '/v1/quote':
                        query = parse_qs(urlsplit(self.path).query)
                        self.reply(200, service.quote(query.get('banner_id',[''])[0], query.get('offer',['primary'])[0]))
                    elif path in ('/v1/state', '/v1/units', '/v1/results'):
                        state = service.state()
                        # Names are a display projection, never a gameplay mutation.
                        for unit in state['units']:
                            unit['name'] = service.gacha.unit_name(unit['master_id']) or unit['master_id']
                        if path == '/v1/units':
                            state = {'units': state['units']}
                        elif path == '/v1/results':
                            state = {'last_pull': state['last_pull']}
                        self.reply(200, state)
                    else:
                        self.error(404, 'not_found', 'Unknown endpoint')
            except Exception:
                logging.exception('GET failed')
                self.error(500, 'internal_error', 'Could not read campaign')

        def do_POST(self):
            if urlsplit(self.path).path != '/v1/summons':
                self.error(404, 'not_found', 'Unknown endpoint')
                return
            if self.headers.get('Transfer-Encoding'):
                self.error(400, 'invalid_request', 'Transfer-Encoding is unsupported')
                return
            if self.headers.get_content_type() != 'application/json':
                self.error(415, 'invalid_content_type', 'Send application/json')
                return
            try:
                length = int(self.headers.get('Content-Length', '-1'))
                if not 0 < length <= MAX_BODY:
                    self.error(413 if length > MAX_BODY else 400, 'invalid_length', 'Body must be 1–4096 bytes')
                    return
                raw = self.rfile.read(length)
                body = json.loads(raw)
                if (not isinstance(body, dict) or set(body) - {'banner_id', 'offer'}
                        or not isinstance(body.get('banner_id'), str)
                        or not 0 < len(body['banner_id']) <= 128
                        or body.get('offer', 'primary') not in ('primary', 'secondary')):
                    raise ValueError('Expected banner_id string and primary/secondary offer')
            except (ValueError, UnicodeError, TimeoutError) as error:
                self.error(400, 'invalid_request', str(error))
                return
            try:
                response = service.summon(body['banner_id'], body.get('offer', 'primary'))
                self.reply(200, response)
            except SummonError as error:
                status = {'unknown_banner': 404, 'invalid_offer': 400,
                          'unsupported_banner': 422, 'summon_refused': 409,
                          'save_failed': 500}.get(error.code, 500)
                self.error(status, error.code, str(error))
            except Exception:
                logging.exception('Summon failed')
                self.error(500, 'internal_error', 'Summon failed; refresh saved state before trying again')

        def do_PUT(self):
            self.error(405, 'method_not_allowed', 'Use GET or POST')
        do_DELETE = do_PATCH = do_PUT

    return ThreadingHTTPServer((host, port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--demo', action='store_true')
    mode.add_argument('--data', type=Path)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[1] / '.local/http-demo')
    parser.add_argument('--save', type=Path)
    parser.add_argument('--initial-lapis', type=int)
    parser.add_argument('--host', type=private_address, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if args.demo:
        from demo_data import prepare
        data = prepare(args.workspace / 'data')
    else:
        data = args.data
    save = args.save or args.workspace / ('campaign.json' if args.demo else 'preserved-campaign.json')
    service = SummonService(data, save, demo=args.demo,
        initial_lapis=args.initial_lapis if args.initial_lapis is not None else (10000 if args.demo else 0))
    with make_server(service, args.host, args.port) as server:
        print('Development API: http://%s:%s; save: %s' % (*server.server_address, save), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()

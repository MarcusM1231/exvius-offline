"""In-process JSON boundary; no HTTP, sockets, new gameplay rules, or RNG."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'prototype'))
from summon_service import SummonError, SummonService

_service = None
_storage = None
_network_guard_installed = False


def _guard_network(event, args):
    if event.startswith('socket.') or event in ('subprocess.Popen', 'os.system', 'os.fork', 'os.posix_spawn'):
        raise RuntimeError('Network and child processes are disabled in the offline backend')


def install_offline_guard():
    global _network_guard_installed
    if not _network_guard_installed:
        sys.addaudithook(_guard_network)
        _network_guard_installed = True


def initialize(data, storage):
    global _service, _storage
    data, storage = Path(data).resolve(), Path(storage).resolve()
    # A bundle path can never be a writable state root.
    if storage == data or data in storage.parents:
        raise ValueError('Save storage must be outside bundled metadata')
    if _service is not None:
        if storage != _storage or data != _service.data_root:
            raise ValueError('One offline campaign per interpreter; restart to change roots')
        return
    install_offline_guard()
    storage.mkdir(parents=True, exist_ok=True)
    save = storage / 'campaign.json'
    # Legacy load can recover a malformed JSON file as a fresh campaign. Preserve
    # the file and surface an error here rather than silently resetting progress.
    if save.exists():
        saved = json.loads(save.read_text(encoding='utf-8'))
        if not isinstance(saved, dict) or not isinstance(saved.get('roster'), list):
            raise ValueError('Invalid campaign file; preserve it and restore a backup')
    service = SummonService(data, save, demo=True, initial_lapis=10000)
    service.data_root = data
    _service, _storage = service, storage


def banners():
    with _service.lock:
        rows = _service.banners()
        for banner in rows:
            banner['offer_details'] = []
            if banner['supported']:
                for offer in banner['offers']:
                    details = _service.details(banner['id'], offer)
                    banner['offer_details'].append(dict(offer=offer,
                        **{k: details[k] for k in ('cost', 'draws', 'guarantee')}))
        return {'banners': rows}


def state():
    with _service.lock:
        result = _service.state()
        for unit in result['units']:
            unit['name'] = _service.gacha.unit_name(unit['master_id']) or unit['master_id']
        if result['last_pull']:
            for award in result['last_pull']['awards']:
                award['name'] = _service.gacha.unit_name(award['unit_id']) or award['unit_id']
        return result


def dispatch(request_json):
    """Return owned JSON text so no Python object crosses the native boundary."""
    try:
        request = json.loads(request_json)
        if not isinstance(request, dict):
            raise ValueError('Expected request object')
        operation = request.get('operation')
        if operation == 'hello':
            value = {'message': 'Hello from embedded Python', 'version': sys.version,
                     'platform': sys.platform, 'answer': 6 * 7}
        elif operation == 'initialize':
            initialize(request['data'], request['storage'])
            value = {'ready': True, 'network_disabled': True}
        elif _service is None:
            raise ValueError('Initialize offline storage first')
        elif operation == 'banners':
            value = banners()
        elif operation == 'state':
            value = state()
        elif operation == 'diagnostics':
            import socket
            rejected = []
            for action in (lambda: socket.socket(), lambda: socket.getaddrinfo('example.com', 80)):
                try:
                    result = action()
                    if hasattr(result, 'close'):
                        result.close()
                    rejected.append(False)
                except RuntimeError:
                    rejected.append(True)
            value = {'network_rejected': all(rejected), 'save': str(_service.save_path),
                     'metadata': str(_service.data_root), 'platform': sys.platform}
        elif operation == 'summon':
            banner, offer = request.get('banner_id'), request.get('offer', 'primary')
            if not isinstance(banner, str) or not 0 < len(banner) <= 128:
                raise ValueError('Expected banner_id string')
            if offer not in ('primary', 'secondary'):
                raise ValueError('Expected primary or secondary offer')
            value = _service.summon(banner, offer)
        else:
            raise ValueError('Unknown offline operation')
        return json.dumps({'ok': True, 'value': value}, allow_nan=False)
    except SummonError as error:
        return json.dumps({'ok': False, 'error': {'code': error.code, 'message': str(error)}})
    except (ValueError, KeyError, OSError) as error:
        return json.dumps({'ok': False, 'error': {'code': 'offline_error', 'message': str(error)}})
    except Exception:
        import traceback
        traceback.print_exc()
        return json.dumps({'ok': False, 'error': {'code': 'internal_error',
                          'message': 'Offline backend failed; refresh saved state before retrying'}})

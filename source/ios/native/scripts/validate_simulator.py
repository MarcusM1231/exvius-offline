"""Exercise embedded Python in iOS and verify cold-launch persistence.

Uses an isolated diagnostic campaign; never erases the normal app campaign.
Run from Terminal with CoreSimulator access, after building the app.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
import uuid

IOS = Path(__file__).resolve().parents[2]


def sim(*args, check=True):
    return subprocess.run(['xcrun', 'simctl', *map(str,args)], check=check,
                          text=True, capture_output=True, timeout=180)


def wait_report(path, stage):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if path.exists():
            value = json.loads(path.read_text())
            if value['status'] != 'passed':
                raise RuntimeError(value)
            if value.get('stage') == stage:
                return value
        time.sleep(0.5)
    raise TimeoutError('No ' + stage + ' report at ' + str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True, help='Available iPhone Simulator UUID')
    parser.add_argument('--app', type=Path, default=IOS / '.local/OfflineSimulator/Build/Products/Debug-iphonesimulator/FFBERevival.app')
    parser.add_argument('--bundle-id', default='com.example.ffberevival.dev')
    parser.add_argument('--skip-install', action='store_true')
    parser.add_argument('--report', type=Path, default=IOS / '.local/offline-simulator-report.json')
    args = parser.parse_args()
    device, bundle = args.device, args.bundle_id
    if not args.skip_install:
        sim('install', device, args.app.resolve())
    sim('terminate', device, bundle, check=False)
    container = Path(sim('get_app_container', device, bundle, 'data').stdout.strip())
    validation_id = str(uuid.uuid4()).upper()
    folder = container / 'Library/Application Support/FFBERevival/validation' / validation_id
    report = folder / 'report.json'
    try:
        sim('launch', device, bundle, '--offline-self-test', '--validation-id', validation_id)
        first = wait_report(report, 'summon-and-save')
        print('iOS summon and save passed', flush=True)
        sim('terminate', device, bundle)
        save = folder / 'campaign/campaign.json'
        before = save.read_bytes()
        sim('launch', device, bundle, '--offline-self-test-reload', '--validation-id', validation_id)
        second = wait_report(report, 'cold-launch-reload')
        if save.read_bytes() != before:
            raise RuntimeError('Cold launch unexpectedly rewrote campaign')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({'first_launch':first, 'cold_launch':second}, indent=2)+'\n')
        print('iOS cold-launch persistence passed:', args.report)
    finally:
        sim('terminate', device, bundle, check=False)


if __name__ == '__main__':
    main()

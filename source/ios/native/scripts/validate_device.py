"""Install a signed app and validate embedded Python on a connected iPhone.

Uses a new diagnostic campaign UUID and leaves the normal campaign untouched.
Requires an unlocked, trusted development device and a signed .app build.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
import uuid

IOS = Path(__file__).resolve().parents[2]


def find_pid(value):
    if isinstance(value, dict):
        if 'processIdentifier' in value:
            return value['processIdentifier']
        for child in value.values():
            found = find_pid(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_pid(child)
            if found is not None:
                return found
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True, help='CoreDevice identifier from xcrun devicectl list devices')
    parser.add_argument('--app', type=Path, default=Path('/private/tmp/FFBERevival-Device/Build/Products/Debug-iphoneos/FFBERevival.app'))
    parser.add_argument('--bundle-id', default='com.example.ffberevival.dev')
    parser.add_argument('--skip-install', action='store_true')
    args = parser.parse_args()
    validation_id = str(uuid.uuid4()).upper()
    logs = IOS / '.local/device-validation' / validation_id
    logs.mkdir(parents=True)
    command_number = 0

    def control(*words, check=True):
        nonlocal command_number
        command_number += 1
        output = logs / ('command-%02d.json' % command_number)
        result = subprocess.run(['xcrun','devicectl',*map(str,words),'--timeout','60',
                                 '--json-output',str(output)], text=True, capture_output=True, timeout=75)
        if check and result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        return result, json.loads(output.read_text()) if output.exists() else {}

    def launch(flag):
        # Global output options precede passthrough application arguments.
        nonlocal command_number
        command_number += 1
        output = logs / ('command-%02d.json' % command_number)
        result = subprocess.run(['xcrun','devicectl','device','process','launch',
            '--device',args.device,'--terminate-existing','--timeout','60','--json-output',str(output),
            args.bundle_id, flag, '--validation-id',validation_id], text=True,capture_output=True,timeout=75)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        pid = find_pid(json.loads(output.read_text()))
        if pid is None:
            raise RuntimeError('No process identifier in ' + str(output))
        return pid

    relative = 'Library/Application Support/FFBERevival/validation/' + validation_id

    def copy_file(name, target, check=True):
        result, _ = control('device','copy','from','--device',args.device,
            '--domain-type','appDataContainer','--domain-identifier',args.bundle_id,
            '--source',relative + '/' + name,'--destination',target,check=check)
        return result.returncode == 0

    def report(stage):
        deadline = time.monotonic() + 90
        target = logs / 'report.json'
        while time.monotonic() < deadline:
            target.unlink(missing_ok=True)
            if copy_file('report.json', target, check=False):
                value = json.loads(target.read_text())
                if value.get('status') != 'passed':
                    raise RuntimeError(value)
                if value.get('stage') == stage:
                    return value
            time.sleep(1)
        raise TimeoutError('No physical-device ' + stage + ' report')

    if not args.skip_install:
        subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(args.app)],check=True)
        control('device','install','app','--device',args.device,args.app.resolve())
        print('Signed app installed on the physical device',flush=True)
    pid = None
    try:
        pid = launch('--offline-self-test')
        first = report('summon-and-save')
        print('Physical-device Python, summons, guarantees and network guard passed',flush=True)
        copy_file('campaign/campaign.json', logs / 'before-relaunch.json')
        control('device','process','terminate','--device',args.device,'--pid',pid,'--kill')
        pid = None
        pid = launch('--offline-self-test-reload')
        second = report('cold-launch-reload')
        copy_file('campaign/campaign.json', logs / 'after-relaunch.json')
        if (logs / 'before-relaunch.json').read_bytes() != (logs / 'after-relaunch.json').read_bytes():
            raise RuntimeError('Cold launch unexpectedly rewrote campaign')
        result = {'first_launch':first,'cold_launch':second,'device_identifier':args.device,
                  'note':'Phone reboot and Airplane Mode are separate manual checks.'}
        output = IOS / '.local/offline-device-report.json'
        output.write_text(json.dumps(result,indent=2)+'\n')
        print('Physical-device force-quit/relaunch persistence passed:',output,flush=True)
    finally:
        if pid is not None:
            control('device','process','terminate','--device',args.device,'--pid',pid,'--kill',check=False)


if __name__ == '__main__':
    main()

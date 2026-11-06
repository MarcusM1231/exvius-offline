"""Simulator UI checks/screenshots using isolated, real Python campaigns only."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',required=True)
    parser.add_argument('--app',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    bundle='com.example.ffberevival.dev'
    def sim(*words):return subprocess.run(['xcrun','simctl',*map(str,words)],check=True,capture_output=True,text=True,timeout=120)
    sim('install',args.device,args.app)
    data=Path(sim('get_app_container',args.device,bundle,'data').stdout.strip())
    report=data/'Library/Application Support/FFBERevival/validation/summon-ui-report.json'
    for page in ['banners','details','confirmation','results','missing-assets']:
        report.unlink(missing_ok=True)  # Diagnostic report only, never a campaign.
        flags=['--summon-ui-diagnostics','--ui-page',page if page!='missing-assets' else 'details']
        if page=='missing-assets':flags.append('--ui-assets-missing')
        sim('launch','--terminate-running-process',args.device,bundle,*flags)
        deadline=time.monotonic()+90
        while not report.exists():
            if time.monotonic()>deadline:raise TimeoutError('UI diagnostic did not finish: '+page)
            time.sleep(0.5)
        value=json.loads(report.read_text())
        if value['status']!='passed':raise RuntimeError(value)
        shutil.copy2(report,args.output/(page+'.json'))
        time.sleep(1)
        sim('io',args.device,'screenshot',args.output/(page+'.png'))
        print('Passed isolated UI page:',page,flush=True)
    sim('launch','--terminate-running-process',args.device,bundle)

if __name__=='__main__':main()

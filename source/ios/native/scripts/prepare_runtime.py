"""Fetch the pinned iOS runtime into ignored .local; verify before extraction."""
import hashlib
from pathlib import Path
import tarfile
import urllib.request

IOS = Path(__file__).resolve().parents[2]
ROOT = IOS / '.local/runtime'
URL = 'https://github.com/beeware/Python-Apple-support/releases/download/3.13-b13/Python-3.13-iOS-support.b13.tar.gz'
SHA256 = 'd1f95f95137a4b91dc0cbe9b99ddfc0a78918dde883c7fbe7147074a5e715274'


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    archive = ROOT / 'python-ios.tar.gz'
    if not archive.exists():
        print('Downloading', URL, flush=True)
        partial = archive.with_suffix('.download')
        urllib.request.urlretrieve(URL, partial)
        partial.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise SystemExit('Runtime checksum mismatch; delete the archive and retry')
    with tarfile.open(archive) as source:
        # Python 3.12+ extraction filter also validates runtime symlinks.
        source.extractall(ROOT, filter='data')
    print((ROOT / 'VERSIONS').read_text())
    print('Verified runtime:', ROOT / 'Python.xcframework')


if __name__ == '__main__':
    main()

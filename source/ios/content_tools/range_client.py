"""Bounded, throttled public-release reads. No retry loops or full-download fallback."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time


class RangeError(RuntimeError):
    pass


class RangeClient:
    def __init__(self, interval=1.0, max_bytes=16 * 1024 * 1024, journal=None):
        self.interval = max(0.5, interval)
        self.max_bytes = max_bytes
        self.transferred = 0
        self.last_request = 0
        self.resolved = {}
        self.requests = []
        self.journal = Path(journal) if journal else None

    def read(self, source, offset, length):
        total = source['archive_size']
        if not 0 < length <= 1024 * 1024 or offset < 0 or offset + length > total:
            raise RangeError('Refusing out-of-bounds or oversized range')
        if self.transferred + length > self.max_bytes:
            raise RangeError('Archive transfer budget reached; resume later from the cache')
        delay = self.interval - (time.monotonic() - self.last_request)
        if delay > 0:
            time.sleep(delay)
        key = source['archive']
        url = self.resolved.get(key, source['url'] + '?ffbe-range=' + str(time.time_ns()))
        with tempfile.TemporaryDirectory() as temp:
            headers, body = Path(temp) / 'headers', Path(temp) / 'body'
            args = ['/usr/bin/curl', '--silent', '--show-error', '--location', '--max-time', '45',
                    '--max-filesize', str(1024 * 1024), '--header', 'Accept-Encoding: identity',
                    '--header', 'Cache-Control: no-cache', '--range', '%s-%s' % (offset, offset + length - 1),
                    '--dump-header', str(headers), '--output', str(body),
                    '--write-out', '%{http_code}\n%{url_effective}', url]
            result = subprocess.run(args, capture_output=True, timeout=50)
            self.last_request = time.monotonic()
            text = headers.read_text(errors='replace') if headers.exists() else ''
            status, _, effective = result.stdout.decode(errors='replace').partition('\n')
            received = body.stat().st_size if body.exists() else 0
            self.transferred += received
            self.requests.append({'archive': key, 'start': offset, 'length': length,
                                  'received': received, 'http_status': status})
            if self.journal:
                self.journal.parent.mkdir(parents=True, exist_ok=True)
                self.journal.write_text(json.dumps({'bytes': self.transferred, 'requests': self.requests}, indent=2))
            if status == '429' or re.search(r'HTTP/\S+ 429', text):
                retry = re.findall(r'retry-after:\s*([^\r\n]+)', text, re.I)
                raise RangeError('HTTP 429: stopped. Retry-After: ' + (retry[-1] if retry else 'not specified'))
            expected = 'bytes %s-%s/%s' % (offset, offset + length - 1, total)
            ranges = re.findall(r'content-range:\s*([^\r\n]+)', text, re.I)
            if result.returncode or status != '206' or not ranges or ranges[-1] != expected or received != length:
                raise RangeError('Exact HTTP range unavailable; stopped without a full-download fallback (HTTP %s)' % status)
            # Reuse a public signed CDN URL in memory; never put its token in receipts/logs.
            if effective.startswith('https://release-assets.githubusercontent.com/'):
                self.resolved[key] = effective
            return body.read_bytes()

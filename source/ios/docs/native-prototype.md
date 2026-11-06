# Phase 3: native summon prototype

This guide covers the preserved Phase 3 HTTP development mode. The current native
project also embeds Python and defaults to offline mode; see
[offline-backend.md](offline-backend.md) for required runtime setup before building
a fresh checkout. Select HTTP development in the app to follow this guide.
No client IPA, Android integration changes, or proprietary artwork are involved.

## Start the backend

From the repository root, with Python 3.10+ installed (3.12 recommended):

```sh
python3.12 -m venv source/ios/.venv
source/ios/.venv/bin/python -m pip install -r source/ios/requirements-smoke.txt
source/ios/.venv/bin/python -B source/ios/prototype/summon_api.py --demo
```

The default address is `http://127.0.0.1:8765`. The Simulator shares the Mac's
loopback networking. A new demo campaign starts with 10,000 free Lapis. Restarting
never refills it. Saves live in ignored `source/ios/.local/http-demo/campaign.json`.
Use a different `--workspace PATH` for an independent campaign. Do not use the CLI
or another backend process against this save while the server is running.

With preserved metadata use `--data /absolute/path/to/data --save /path/to/separate/campaign.json`;
`--initial-lapis 10000` seeds only a new campaign. There is no automatic demo fallback.
Demo metadata uses placeholder names and starter records; it does not prove playable
units or battle compatibility. Existing supported banner types remain unchanged.

## Open and run in Xcode

Open `source/ios/native/FFBERevival.xcodeproj`. Select the FFBERevival scheme and
an installed iPhone Simulator, then Run. Press **Connect / Refresh saved state**.
Select a priced offer, inspect the latest saved summon, and open Collection.
Prices and draw counts come from Python; Swift owns no gameplay calculations.

XcodeGen is not required. Regenerate the checked-in project after adding Swift files:

```sh
python3 source/ios/native/generate_project.py
```

The generator uses only Python's standard library, sorted input filenames and stable
IDs. Signing settings are local Xcode choices; do not commit personal team IDs or
certificates. To build without signing:

```sh
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -configuration Debug \
  -derivedDataPath source/ios/.local/DerivedData CODE_SIGNING_ALLOWED=NO build
```

## Run on your iPhone

1. Put the Mac and iPhone on the same trusted Wi-Fi network.
2. Find the Mac's Wi-Fi IPv4 address in System Settings → Wi-Fi → Details → TCP/IP.
3. Stop the loopback server and start it explicitly on that address:
   `source/ios/.venv/bin/python -B source/ios/prototype/summon_api.py --demo --host 192.168.1.20`
   (replace the example address with the Mac's actual address).
4. In Xcode select your connected iPhone, set your signing team and a unique bundle
   identifier in Signing & Capabilities, enable Developer Mode on the phone if asked,
   then Run. Allow Python's local incoming connection in the Mac firewall if prompted.
5. Enter `http://192.168.1.20:8765` in the app and press Connect. Allow local-network
   access when prompted. If previously denied, enable it in iOS Settings for the app.

Local-network usage text and the local HTTP ATS exception are in Info.plist.
Only explicit loopback or RFC1918 IPv4 binds are accepted; wildcard/public binds
are rejected. There is no authentication or TLS: use this only on trusted local
Wi-Fi, with no router forwarding, public proxy, tunnel, or public deployment.
Guest Wi-Fi/client isolation and VPN routing may prevent devices from connecting.
This phase intentionally requires the running Mac and local network.

## API contract

All routes return JSON, with `Cache-Control: no-store`.

| Method | Path | Success |
| --- | --- | --- |
| GET | `/v1/banners` | `{banners:[...]}`, including backend-derived `offer_details` |
| GET | `/v1/state` | `{demo_metadata,currencies,units,last_pull}` |
| GET | `/v1/units` | `{units:[...]}`, display names added to copied records |
| GET | `/v1/results` | `{last_pull:...}` (null before first summon) |
| POST | `/v1/summons` | `{result,state}` after saving |

POST requires `Content-Type: application/json`, a body up to 4096 bytes and
`{"banner_id":"9100203","offer":"primary"}`. Offer defaults to primary. There are
no arbitrary repetitions, client prices, grants, or balances. Errors are
`{"error":{"code":"...","message":"..."}}`. Validation errors use 400, unknown
routes/banners 404, oversized requests 413, content-type errors 415, unsupported
banners 422, refused transactions 409, and save/internal failures 500. A refusal
can mean insufficient currency, a limit, or unavailable pool; the API preserves
that distinction rather than inventing a precise cause.

The threaded listener shares one SummonService and its existing reentrant lock;
mutations are serialized and failed saves roll back through the facade. One
process must own each campaign; there is no cross-process writer lock. Read
projections are copied under the same lock. Backend errors are logged server-side
without exposing traces to the app. This is a small development server.

POSTs are not idempotent. The app disables overlapping operations and does not
retry summons automatically. After any summon error it blocks further pulls until
a successful refresh: a lost response may follow an already persisted transaction.
Latest results are restored from `last_pull`; this is not a full summon history.

## Verify

Run each backend suite as its own process (the engine binds one data root):

```sh
source/ios/.venv/bin/python -B source/ios/tests/test_summon_service.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_api.py
source/ios/.venv/bin/python -B source/ios/tests/smoke_backend.py
# macOS + Xcode: compile the actual Swift client and exercise URLSession
source/ios/.venv/bin/python -B source/ios/tests/test_native_client.py
```

Device acceptance: connect, pull once (10,000 → 9,500 on a fresh demo campaign),
verify one added unit, force-close and reopen the app, reconnect and verify the
same balance/results/collection. Restart Python and reconnect; verify persistence.
Try an eleven-pull and a refused pull. Stop Python and check the connection error.
An unsigned build alone does not establish device networking or signing success.

The next phase can replace URLSession transport with a serialized on-device Python
bridge while retaining SummonService. Battles still require a viable frontend.

## Validation recorded on this Mac

- Xcode 26.2 unsigned Debug Simulator build: passed (arm64 and x86_64).
- Existing summon service: 7 tests passed.
- HTTP integration: 5 tests passed, including 24 concurrent attempts with only
  20 affordable transactions accepted and no overdraw.
- Existing backend smoke test: passed.
- Actual Swift URLSession client against a real isolated Python demo service:
  passed banner decoding, summon, debit, collection and saved-result refresh.
- Simulator launch was unavailable because CoreSimulatorService was inaccessible
  in this session. Physical-device execution, signing and local-network permission
  are still to be verified by the device acceptance steps above.

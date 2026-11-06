# Phase 4: on-device Python summoning

Phase 5B adds a separate read-only names/artwork catalog. Current builds also need
the import described in [unit-content.md](unit-content.md); the engine/save boundary
below remains unchanged.

The app defaults to **On-device Python**. SwiftUI calls a bundled CPython interpreter
through a small Objective-C C-API bridge. There is no local listener, HTTP request,
Mac service, downloaded script, or internet connection in this mode. The original
`PlayerState.roll_gacha()` remains responsible for costs, RNG, guarantees, awards,
counters, and state. This phase covers the two existing demo banners and collection
viewer, not playable battles or a complete FFBE port.

## Feasibility and runtime choice

| Approach | Assessment for this project |
| --- | --- |
| BeeWare Python-Apple-support + CPython C API | Selected. Supplies an iOS XCFramework and native standard-library extensions; lets us keep SwiftUI and the existing Python service. |
| Build CPython for iOS from source | Supported upstream route; adds cross-compilation and dependency maintenance. No benefit for this first small slice while a tested prebuilt runtime is available. |
| PythonKit | A Swift convenience layer over an interpreter, not an iOS runtime. It would still require the runtime, path setup, packaging, and signing. The small JSON boundary needs no extra dependency. |
| Kivy/kivy-ios | Provides an iOS packaging toolchain, but introduces another application/UI toolchain. We already have a working native SwiftUI app. Not built or certified here. |
| Rewrite summoning in Swift | Unnecessary for this slice and risks diverging from the existing transactions. Not implemented. |

Primary sources consulted:
[CPython's iOS embedding guide](https://docs.python.org/3.13/using/ios.html),
[BeeWare runtime and build documentation](https://github.com/beeware/Python-Apple-support),
[BeeWare usage guide](https://github.com/beeware/Python-Apple-support/blob/3.13/USAGE.md),
[PythonKit](https://github.com/pvieito/PythonKit), and
[Kivy iOS packaging](https://kivy.org/doc/stable/guide/packaging-ios.html).

The pinned [BeeWare 3.13-b13 release](https://github.com/beeware/Python-Apple-support/releases/tag/3.13-b13)
contains CPython **3.13.11**, a device arm64 slice, and arm64/x86_64 Simulator slices.
Its manifest specifies iOS 13 minimum; our app targets iOS 16+. Inspection of the
device Mach-O shows `platform IOS`, minimum 13.0, SDK 18.5. The runtime's existing
SDK version is not a substitute for testing with our Xcode: Xcode 26.2 device and
Simulator builds are checked separately. The interpreter is bundled under ignored
`.local/`, rather than committed as a binary dependency. A pinned download with a
SHA-256 check makes setup reproducible; upgrading the runtime requires repeating
the execution and signing checks, rather than silently changing versions.

### Dependency scope

A real import trace of initialization, banner display, and summons loads six server
modules: `player_state`, `data_paths`, `ffbe_config`, `ffbe_state`, `ffbe_gacha`, and
`season`. This slice needs only the standard library, including compiled standard
modules such as `_random`, `_json`, and `math`. They are packaged from the iOS
runtime; desktop extension modules are never copied into the app.

The larger request pipeline also uses `cryptography` and PyYAML. They are **not
replaced, stubbed, or imported by the offline summon slice**. PyYAML has a pure
Python implementation that can avoid its optional LibYAML extension. Cryptography
requires iOS-compatible native/Rust/OpenSSL components and their packaging; its
macOS wheels cannot run on iPhone. The existing `openssl` subprocess fallback is
not viable inside iOS. These larger paths have not been integrated or certified.
Desktop Phase 1 smoke tests still exercise the full pipeline with desktop dependencies.

## Architecture and ownership

```text
SwiftUI -> SummonModel -> SummonBackend
                         |-> HTTPBackend -> URLSession -> existing Mac HTTP API
                         `-> EmbeddedSummonBackend actor
                              -> shared serial PythonWorker queue
                              -> PythonBridge.m (CPython C API + GIL)
                              -> offline_entry.dispatch(JSON)
                              -> existing SummonService
                              -> existing PlayerState.roll_gacha / save / load
```

`SummonBackend` exposes catalogue, state, and summon operations. The shared models
and UI work with either implementation. Legacy HTTP entry points remain available,
including their existing client test. HTTP mode is selected explicitly in the app's
Backend picker; it retains the editable development address and local-network
permission text. **It uses a separate campaign on the Mac.** No progress is silently
migrated from Phase 3 or shared between the two modes.

The interpreter is initialized once using isolated `PyPreConfig`/`PyConfig`, explicit
bundled search paths, UTF-8, unbuffered logs, no bytecode writes, and no environment
or user-site search paths. Initialization runs off the main thread. The initial GIL
is released with `PyEval_SaveThread`; subsequent calls acquire/release the GIL because
a serial dispatch queue may use different OS threads. The interpreter remains alive
for the process lifetime, even when switching to HTTP. Python objects and borrowed
pointers never escape the bridge: the bridge returns owned NSString JSON. Swift
updates observable UI state on the main actor.

`offline_entry.py` translates only operations, JSON, display names, and errors. It
uses the facade's existing reentrant lock and save/rollback behavior. It does not
select units, calculate probabilities, grant rewards, or modify prices. The Swift
award decoder accepts both numeric and numeric-string rarities from the legacy
backend; duplicate awards exposed this difference during end-to-end testing.

An interpreter audit hook rejects socket creation, DNS operations, and child-process
execution. On-device diagnostics actively test these rejections. This is a guard
against accidental Python network dependencies, not a security sandbox for arbitrary
code. Native URLSession remains usable only through explicit HTTP development mode.

## Bundled resources and native saves

The build phase generates synthetic metadata using the existing `demo_data.prepare()`
and copies it into `FFBERevival.app/PythonApp/metadata/demo`. It also copies the six
unchanged Python modules and required existing JSON content, maintaining the service's
relative `source/server` path contract. Nothing is fetched or generated on the phone.
Code, metadata, and the standard library remain in the signed read-only bundle.
Build-time packaging does not read personal IPAs, game assets, or Android saves.

The normal on-device save is:

```text
<Application Support>/FFBERevival/offline-demo-v1/campaign.json
```

Swift obtains Application Support through FileManager, creates the directory, and
sets protection to complete-until-first-user-authentication on iOS. The save file
is passed explicitly to SummonService; no bundle path is used for saving. A new
campaign receives 10,000 free Lapis once. Existing campaigns are never refilled.
Initialization validates existing JSON before legacy loading, so a malformed or
unreadable save is surfaced and preserved rather than reset to a fresh account.

The existing save operation writes a temporary file then replaces the campaign;
failed writes roll back the facade's in-memory transaction. Normal app termination
and reboot should preserve Application Support, and must be checked on the physical
phone. This does not add a guarantee against sudden power loss during a disk write.
Deleting the app deletes its local save. Demo campaigns are development-only records,
not a migration format for the future game. Real preserved metadata and richer
collection management remain separate follow-up work.

## Framework packaging and signing

`package_python.py` copies the shared and target-specific standard library. For
universal Simulator builds it combines matching extension binaries with lipo. Each
native `.so` becomes a separate framework in the app's Frameworks folder, with
`.fwork` markers and `.origin` references understood by CPython's AppleFrameworkLoader.
This follows the upstream layout while keeping architecture selection explicit.
The Python interpreter is linked and embedded through Xcode's XCFramework support.

For signed device builds, the build phase signs every extension framework using
Xcode's selected identity; Xcode embeds/signs Python.framework and the app. An
unsigned device build deliberately skips signing and **cannot be installed as-is**.
No jailbreaking, JIT entitlement, executable downloads, or dynamic code generation
is required. Bundled Python source is interpreted as data by the signed interpreter.
Sideloading still requires a valid development signing identity and provisioning.
No App Store review or distribution claim is made.

`Build.xcconfig` includes an optional ignored `Signing.local.xcconfig`. Put personal
team/bundle settings there; regeneration then preserves them. The existing local
signing team was recovered from this Mac's Phase 3 Xcode build cache and placed
there. No personal signing identity or runtime binary belongs in a commit.

## Exact setup and build commands

From the repository root:

```sh
cd ~/Documents/Projects/exvius-offline
git branch --show-current  # must be ios-port
# Only if the desktop environment does not already exist:
python3.12 -m venv source/ios/.venv
source/ios/.venv/bin/python -m pip install -r source/ios/requirements-smoke.txt

# One-time runtime download (requires internet on the build Mac):
source/ios/.venv/bin/python -B source/ios/native/scripts/prepare_runtime.py
python3 source/ios/native/generate_project.py

# Compile/link the actual arm64 device target without accessing signing accounts:
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Device \
  CODE_SIGNING_ALLOWED=NO build

# Simulator (both available framework CPU architectures):
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Simulator \
  CODE_SIGNING_ALLOWED=NO build

open source/ios/native/FFBERevival.xcodeproj
```

Keep signed build output outside iCloud-synced Documents. On this Mac, Finder
metadata appeared on generated framework folders under Documents and caused the
final codesign step to fail; building in `/private/tmp` fixed it. The source
checkout stays in place. Xcode’s normal DerivedData location is also appropriate.

Python 3.12+ is required for the runtime preparation script's safe archive extraction;
the Xcode package phase uses the Mac's existing `/usr/bin/python3`. Runtime and
metadata are already prepared on this Mac. Do not delete `.local/runtime` before
building; missing runtime files produce a setup error. The download is never part
of app startup or a runtime network dependency.

For signing on another Mac, create `source/ios/native/Signing.local.xcconfig` with:

```xcconfig
DEVELOPMENT_TEAM = YOUR_TEAM_ID
// Optional if your signing setup needs a different identifier:
PRODUCT_BUNDLE_IDENTIFIER = com.yourname.ffberevival
```

Select your iPhone 16 Pro in Xcode and Run. Xcode may request the usual account,
Developer Mode, trust, or signing setup. Keep the same app identifier for updates
to retain its on-device save; do not uninstall it when testing persistence.

## Automated checks

Run suites as separate processes because the backend binds one data root per
interpreter:

```sh
source/ios/.venv/bin/python -B source/ios/tests/test_summon_service.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_api.py
source/ios/.venv/bin/python -B source/ios/tests/smoke_backend.py
source/ios/.venv/bin/python -B source/ios/tests/test_native_client.py
source/ios/.venv/bin/python -B source/ios/tests/test_offline_entry.py
```

The offline suite packages the actual minimal resources, then uses isolated fresh
Python processes with site-packages disabled. It tests real transactions, guarantees,
collection updates, fresh-process persistence, failed-save rollback, corrupt-save
preservation, unchanged bundled resources, input validation, and rejection of network
and subprocess operations. This desktop suite alone does not prove iOS execution.

To execute in iOS, boot an installed iPhone Simulator in Xcode, find its UUID with
`xcrun simctl list devices available`, then run:

```sh
source/ios/.venv/bin/python -B source/ios/native/scripts/validate_simulator.py \
  --device YOUR_SIMULATOR_UUID \
  --app /private/tmp/FFBERevival-Simulator/Build/Products/Debug-iphonesimulator/FFBERevival.app
```

The runner installs the built app and launches an isolated diagnostic campaign.
Swift invokes embedded Python, loads banners, spends 500 for one unit, spends 5,000
for eleven, checks the guarantee, refuses another unaffordable eleven-pull, and
verifies 4,500 Lapis/14 owned units/11 latest awards. It terminates and relaunches
the app and checks those values again, including unchanged save bytes on reload.
The report is written to ignored `.local/offline-simulator-report.json`. Diagnostic
campaigns live under `Application Support/FFBERevival/validation/<UUID>/campaign`;
the normal offline campaign is never erased or used by these tests.

## Automated physical-device checks

With the phone connected/unlocked and the existing signing setup available, build
without `CODE_SIGNING_ALLOWED=NO`:

```sh
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Device build
xcrun devicectl list devices
source/ios/.venv/bin/python -B source/ios/native/scripts/validate_device.py \
  --device YOUR_COREDEVICE_IDENTIFIER
```

The device runner verifies the signature, installs the app as an update, and uses
a new isolated validation campaign. It copies structured diagnostic reports out of
the app container and compares save bytes before and after a SIGKILL/relaunch.
It does not change connectivity settings or reboot the phone. Reports are in
`.local/offline-device-report.json` and `.local/device-validation/`. The normal
local campaign and Mac campaign are not used for diagnostic summons.

## iPhone 16 Pro acceptance checklist

1. Build and Run on the actual phone through Xcode. Confirm On-device Python mode,
   both banners, and a Python proof reporting `ios`, version 3.13.11, and answer 42.
2. Stop the Mac HTTP backend. Disconnect the USB cable. Enable Airplane Mode and
   explicitly turn Wi-Fi off (Airplane Mode can retain Wi-Fi).
3. On a new local demo campaign, pull once: 10,000 → 9,500 Lapis; collection 2 → 3.
4. Pull eleven: 9,500 → 4,500; collection 3 → 14; eleven latest awards with at least
   one rarity 4+. Another eleven-pull must be refused without changing progress.
5. Force-close from the app switcher. Reopen while still disconnected. Confirm
   4,500 Lapis, 14 owned units and the same latest results. Refresh after a refusal
   if needed before another operation.
6. Restart the phone, unlock it, and launch with network still disabled. Confirm
   the same saved state. Do not delete/reinstall the app as part of this test.
7. Re-enable networking and explicitly select HTTP development mode; confirm the
   Phase 3 Mac campaign still works. Switch back to On-device Python and confirm
   the separate local progress remains.

If you already spent from the local campaign, compare against its starting values
rather than expecting the fresh-account numbers. Runtime diagnostics do not reset it.
Optional: Xcode's scheme launch arguments `--offline-self-test --validation-id <UUID>`
run the isolated checks on the phone too. On the next launch use
`--offline-self-test-reload --validation-id <SAME_UUID>`. Inspect the on-screen report
or Xcode console, then remove these launch arguments for normal use.

Physical-device execution and phone-reboot persistence must not be inferred from a
Simulator run or an unsigned arm64 build. Record them only after these phone checks.

## Validation recorded on this Mac and iPhone

- Runtime archive SHA-256 verified; runtime preparation script executed successfully.
- Xcode 26.2: device arm64 compilation/linking and signed development build passed.
- Xcode 26.2: universal arm64/x86_64 Simulator build passed.
- Embedded Python proof executed in the iOS 26.3 Simulator: `ios`, 3.13.11, answer 42.
- Full Simulator diagnostic and terminate/relaunch persistence passed.
- Signed app installed and executed on the connected **iPhone 16 Pro**; real single
  summon, multi-pull guarantee, refused unaffordable pull, collection updates,
  bundled metadata, Application Support storage and network rejection checks passed.
- The iPhone test used SIGKILL and a new launch; 4,500 Lapis, 14 owned units,
  eleven latest awards and unchanged saved bytes were verified after relaunch.
- Existing service tests: 7 passed; HTTP tests: 5 passed; new isolated offline tests:
  6 passed; existing encrypted backend smoke and real Swift URLSession checks passed.
- Android/server gameplay sources are unchanged. HTTP transport is retained.

The device test initially exposed `/var` versus `/private/var` spellings of the
same save path; the diagnostic now compares canonical resolved paths. The native
multi-pull also exposed legacy mixed rarity types; the shared Swift decoder has
coverage for number, numeric string and null values.

The normal on-device campaign is separate from the test campaigns. Physical
Airplane Mode operation and phone-reboot persistence remain manual checks; no
connectivity settings were changed and the phone was not rebooted automatically.

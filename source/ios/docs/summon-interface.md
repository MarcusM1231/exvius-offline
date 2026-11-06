# Phase 6B — Global summon interface

The Summon tab now uses selected original Global 9.1.0 layout regions and recovered
UI artwork. Banner selection, detail/price buttons, confirmation, saved results and
return navigation use the existing `SummonModel` and backend protocol. Collection,
423 exact-ID sprites and real names remain intact. The previous prototype, Python
proof and HTTP mode remain available in the Developer tab.

There is no crystal effect, simulated upgrade, animation delay, audio playback or
`.bmb` renderer in this phase. A successful backend response goes directly to results.

## Content and provenance

The separate source lock is `content_tools/summon-ui.lock.json`. It selects:

- Original Global IPA: six `layout/gacha/` CSVs (Top, Detail, ResultUnit at
  640×1136; Confirm, ButtonL, ButtonR), `icon_lapis.png`, `window_base.png`,
  `bottomline.png` from the recovered Global CPKs.
- Global-targeted preservation: normal/pressed single and 11-summon button PNGs
  from data-010 `native/en/sd/gacha/Ver58_gacha1.cpk`; selected `gacha` / `gacha2`
  atlas frames and the cosmos background from
  `native/en/sd/resources/Ver162_resources_tutorial.cpk`.
- No Memorial/JP inputs. No NV+ labels, reroll anchors or newer result layouts.

Every source and CPK member has a SHA-256 pin. The importer validates those hashes,
decompresses CRILAYLA if necessary, parses CSV/plist, and decodes PNGs. TexturePacker
legacy and format-3 keys support rotation, trimming, original source dimensions and
exact frame names. It restores upright transparent source canvases as build-time
PNG derivatives; original game files are never edited. Synthetic red/green tests
verify rotation direction and trim placement, independent of the production assets.

Only eleven selected images are bundled. No whole CPK, IPA, source atlas or audio
bank is bundled. The output receipt pins the exact derived bytes. Repeated import
must produce identical files or it refuses to replace an existing version. Tested
import environment: system Python 3.9 with Pillow 9.1.1. Preserve that environment
for identical derivatives; a different imaging-library version must pass the same
reproduction check. Pillow is a build-time dependency, not an iOS runtime dependency.
Xcode uses only Python’s standard library to verify and copy the existing bundle.

The preservation archive caveat from Phase 6A remains: this is verified
Global-targeted content, not proof of original retail Global CDN byte identity.
Exact source locations, provenance and hashes are in the small source lock.

## Recovered elements versus adaptations

| Element | Implementation / limitation |
| --- | --- |
| Layout reference | Direct Global 9.1.0 CSV anchors; no Memorial or later CSV replacement |
| Summon controls | Original single/11-summon normal and pressed artwork; live cost amount in its price region |
| Other offer kinds/counts | Accessible native labeled button; never mislabel a non-11 offer with baked “11 Summons” art |
| Lapis | Original icon, live free+paid balance; backend remains the cost authority |
| Demo banners | Recovered generic gacha background with live banner name and explicit DEMO BANNER label; exact promotional art is unverified |
| Header and tabs | Original line/tab texture, native text/navigation; system serif font replaces unrecovered exact typography |
| Confirmation | Original window surface and native accessible controls in a scrolling sheet; this is an adaptation, not a pixel-exact original modal |
| Results | Recovered cosmos and unit plate, actual awarded IDs/rarities and existing unit sprites; generated adaptive grid is a reconstruction |
| Missing UI resource | Labeled “UI artwork unavailable”; missing catalog enables fallback layout constants and a visible notice |
| Missing unit sprite | Existing exact-ID placeholder; no character-name substitution |
| Reliable results fallback | Original plain `UnitRowView` list, opened from results; reads the same saved awards |

Unused ticket, step-up and panel CSV references are retained as metadata, not rendered.
The lock’s `render_bindings` identifies the actual rendered anchors and their resolved
images or explicit native/demo fallbacks. No unresolved reference silently causes an
unrelated texture lookup. Recover additional exact common skins before claiming a
pixel-exact confirmation/results experience.

## Coordinate conversion and safe areas

CSV values are treated as a reference region map, not blindly assigned to native
SwiftUI points. The selected original canvas is 640×1136. Its old global header band
`y=0...172` is replaced by native safe-area navigation and the live Lapis strip.
Within a scrollable logical canvas:

```
s = min(available safe-area width, 760) / 640
nativeX = (csvX + csvWidth / 2) * s
nativeY = (csvY - 172 + csvHeight / 2) * s
nativeWidth = csvWidth * s
nativeHeight = csvHeight * s
```

The top banner uses `common_banner` (0,338,640,160); details use `gacha_banner`
(0,250,640,392) and left/right summon offsets at y=653. Text/costs are live and
cannot be baked into screenshots. The original button’s price region is used for
the number; the original Lapis icon supplies the currency symbol. Long banner names
wrap. Smaller widths scale uniformly and scroll vertically instead of stretching.

The result area starts from `gacha_result_area2.y=312`, with its old negative x
clamped into safe content bounds. Result tiles adapt to available width because
Phase 6A did not establish the original client-generated multi-result grid. The
confirmation sheet reflows native text and controls, scrolls for long content, and
uses the original window surface; it does not pretend CSV modal positions are
already validated in SwiftUI. Safe areas and the system tab bar stay outside the
logical canvas. The application explicitly uses a dark appearance for readable
text and status/navigation controls.

## Transactions and Phase 6C seam

`SummonModel.summon` now returns an explicit success Boolean. It still makes exactly
one backend call and applies that returned state/award list. Its existing busy and
refresh guards remain. A synchronous UI in-flight latch blocks repeated confirm
callbacks. Failures return false, retain the last saved awards and require a state
refresh before another summon; they do not open a new results screen. Ambiguous
HTTP failures are never automatically retried or charged again by presentation.

The successful-confirm callback is the insertion point for Phase 6C: it currently
sets the result route directly. A future SpriteKit host may consume the already
committed awards there. Its completion, skip or playback failure must all route to
`GlobalSummonResults`/plain saved results without calling `summon` again. Relaunch
reads `campaign.last_pull`, and “View latest saved summon” spends no currency.
Backend-mode changes recreate presentation state so stale selection cannot survive
switching between the device campaign and HTTP development campaign.

The Python facade, `PlayerState`, rates, guarantee rules, transactions, inventory,
metadata and save schema/path are unchanged. No Android source is modified.

## Rebuild and install

From the repository root:

```sh
# Cache-only, no network. Requires the recovered Phase 6A cache and Pillow.
python3 -B source/ios/content_tools/import_summon_ui.py
python3 source/ios/native/generate_project.py

xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6B-Simulator \
  CODE_SIGNING_ALLOWED=NO build

xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6B-Device build

open source/ios/native/FFBERevival.xcodeproj
```

Use the existing local signing team and `com.example.ffberevival.dev` bundle ID.
Select the connected iPhone 16 Pro and Run to update the app. **Never uninstall or
change its bundle ID to test this phase.** Keep personal signing configuration local.
Phase 4 Python runtime and Phase 5C unit-content setup remain prerequisites.

`FFBE_SUMMON_UI=fallback` is an explicit build option for development without the
imported UI bundle; unit metadata/art remains independently packaged. Ordinary
builds fail with a helpful import instruction if UI content is missing/corrupt.
Runtime uses bundled local files only, with no asset-download code.

Cache/backup locations (ignored):

```text
source/ios/.local/phase6a/                       pinned recovered source inputs
source/ios/.local/summon-ui/versions/<lock>/SummonUI/  immutable derived UI bundle
```

```sh
ditto source/ios/.local/phase6a /Volumes/YOUR_BACKUP/FFBERevival/phase6a
ditto source/ios/.local/summon-ui /Volumes/YOUR_BACKUP/FFBERevival/summon-ui
```

Retain the matching lock/source commit and tested import environment. This is a
content backup, not a phone-save backup. No game binary, cache or save belongs in Git.

## Automated and manual validation

```sh
python3 source/ios/tests/test_summon_ui_assets.py
source/ios/.venv/bin/python -B source/ios/tests/test_unit_content.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_service.py
source/ios/.venv/bin/python -B source/ios/tests/test_offline_entry.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_api.py
source/ios/.venv/bin/python -B source/ios/tests/smoke_backend.py
source/ios/.venv/bin/python -B source/ios/tests/test_native_client.py

python3 source/ios/native/scripts/validate_summon_ui.py \
  --device YOUR_SIMULATOR_UUID \
  --app /private/tmp/FFBERevival-Phase6B-Simulator/Build/Products/Debug-iphonesimulator/FFBERevival.app \
  --output /private/tmp/Phase6B-UI-Screenshots
```

The screenshot harness uses explicitly labeled isolated real Python campaigns, not
fabricated rewards or the normal campaign. It verifies single/multi costs, concurrent
submission refusal, insufficient currency retaining saved results, UI dependency
decoding, and 320/393/440/768-point renders. It captures banners, details,
confirmation, real results and intentionally missing-asset mode. On an iPhone, the
same check can run with Xcode launch arguments `--summon-ui-diagnostics --ui-page details`.
Remove all diagnostics arguments for ordinary play. The report is stored under
Application Support `FFBERevival/validation/summon-ui-report.json`.

Manual iPhone checks still required:

1. Confirm existing Lapis and collection are unchanged after the update.
2. Select each banner; check complete names, single/multi counts and displayed cost.
   Open confirmation, then Cancel and verify no charge.
3. If you choose to spend campaign currency, confirm one summon and compare balance,
   awarded units and collection; reopening saved results must not charge again.
4. Background/resume from the Home screen; then force-close and relaunch. Check
   saved results, currency and collection. Repeat after restarting the phone.
5. Enable Airplane Mode **and turn Wi-Fi off**; launch and browse collection/results.
   A chosen summon must still work without the Mac or HTTP server.
6. Rotate/resize where supported, increase text size, and check scrolling/accessibility.

Automated network rejection and force-quit tests do not prove physical radio-off,
phone reboot, manual touch targets, or every accessibility setting was exercised.


## Completed validation — 2026-11-06

- Xcode 26.2: Simulator (arm64/x86_64) and signed arm64 device builds succeeded.
- 32 Python tests passed: UI import 6, unit content 8, summon service 7, offline
  entry 6, HTTP API 5. Backend smoke and Swift HTTP contract checks also passed.
  The smoke test was run in the project virtual environment containing cryptography;
  the system Python lacks that backend dependency and is used only for Pillow import.
- Simulator UI harness passed all five screens/modes. Screenshots were visually
  reviewed and fixes made for long banner wrapping and original-icon price placement.
  Diagnostic transactions and saved results are real, from isolated campaigns.
- Physical iPhone 16 Pro: final UI report passed single/multi costs, concurrent-submit
  guard, refusal preserving saved rewards, eleven decoded UI assets, missing-resource
  handling and four rendered widths. Existing full offline diagnostics additionally
  passed guarantees, network rejection and force-quit/cold-launch persistence on both
  Simulator and physical iPhone.
- The normal iPhone campaign was read before the first update and after all diagnostics
  and normal startup. Its bytes were identical. No normal-campaign summon, reset,
  migration, restore or uninstall was performed. The phone was left in the ordinary app.
- Phase 5C UnitContent remains 1,089,195 bytes; its source lock is unchanged.
- New SummonUI bundle: 1,293,965 bytes (1.23 MiB), eleven derived images plus layout
  catalog/receipt. Signed Debug device app: 41,665,727 bytes versus Phase 5C’s
  39,310,168 bytes, an increase of 2,355,559 bytes (2.25 MiB). Debug code/diagnostics
  are included; this is not a release IPA size measurement.
- No new network retrieval was needed. Original sources/archives, binary assets,
  caches, generated builds and saves remain outside Git. Changes remain uncommitted.

Radio-off launch, actual Home-screen background/resume, reboot, manual confirmation
and cancellation gestures, and every text/accessibility setting remain manual checks
as listed above. No claim is made that these were physically exercised automatically.

Phase 6C readiness: a committed-response presentation boundary, original result art,
exact awarded units/rarities, saved-result recovery and a plain-list fallback are ready.
The `.bmb` renderer, full original crystal state machine, upgrade choreography,
audio synchronization and unverified historical multi-grid remain future work.

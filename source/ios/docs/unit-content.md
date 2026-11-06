# Phase 5B: real names and the first static character sprites

The native app now has a bundled, read-only display catalog derived from the pinned
Global-targeted preservation tables. It displays real names for every current demo
ID, exact-master-ID PNG artwork for Ludmille, Rain and Lasswell, and an explicit
**Art unavailable** placeholder for other forms. This is a small static-art slice;
there are no crystal animations, new battle mechanics or changes to summon odds.

## Coverage

| Coverage | Count |
| --- | ---: |
| Master/form IDs in the supplied table | 3,311 |
| Master IDs with an English name | 3,089 |
| Master IDs without a matching name | 222; shown as Unknown unit (ID) |
| Existing demo IDs with a real name | 423 / 423 |
| Exact form IDs with bundled artwork | 3 |

| ID | Name | Row rarity | Available static art |
| --- | --- | --- | --- |
| `100004203` | Ludmille | 3 | `unit_ills_100004203.png` (65×68) |
| `100000102` | Rain | 2 | `unit_ills_100000102.png` (74×59) |
| `100000202` | Lasswell | 2 | `unit_ills_100000202.png` |

Ludmille is in both existing authored banner pools. The two starter forms are in
the collection. Other IDs, including other forms named Ludmille, do not inherit
these images. Most summons will still have missing artwork in this first slice.
Do not change a banner or spend repeatedly merely to force an illustrated result.

## Why this is a display catalog rather than a gameplay-table replacement

The existing backend continues to own every transaction. The build still packages
the same Phase 4 minimal engine metadata, unchanged authored banners and existing
SummonService. The new catalog is a **presentation projection** of original unit
metadata, indexed by the exact IDs returned by Python. It is bundled alongside,
not substituted into, the engine's tables.

This avoids changing root/form flags, pool expansion, duplicate grants, coherence
validation or saved records while introducing names and pictures. It also gives
HTTP development mode the same local display lookup: no server/API rewrite or
runtime artwork URL is required. The backend's raw `name` may still be a fixture
label in development responses; the native view resolves the authoritative display
name from the separate catalog. Missing real names never fall back to an invented
character name. Explicit demo-content builds may continue to show fixture labels.

The UI displays awarded rarity from the actual summon result, separately from base
rarity and the terminal rarity in the supplied awakening recipe chain. Collection
rarity describes the current master/form row, retaining a saved rarity as a fallback
when no row exists. `instance_id` still identifies each owned copy: duplicates remain
separate rows. No inventory grouping, migration, grant or save write is involved.

The importer reads `3HriTp6B` as the master ID, `woghJa61` as the series/root link,
`9fW0TePj` as the row rarity, and `t74crqAL` in the awakening table as the next master
ID. Missing roots/targets and cycles yield unknown metadata instead of guessed caps.
Rarity codes 1–6 are displayed with stars; code 7 retains a literal code label because
legacy/NV semantics should not be invented from a numeric value alone.

## Source and checksums

`content_tools/content.lock.json` pins five ZIP members from the exact release URLs,
including archive sizes/SHA-256 references, member offsets, sizes, compression methods,
CRC32s and observed expanded-member SHA-256s:

- `exvius-data-001.zip`: `static/mst_decoded/F_UNIT_MST.ndjson`,
  `static/text_decoded/F_TEXT_UNITS_NAME.ndjson`, and
  `static/mst_decoded/F_UNIT_CLASS_UP_MST.ndjson`.
- `exvius-data-008.zip`: `native/common_lang/sd/unit/Ver5_unit2_common_tutorial.cpk`
  and `native/common_lang/sd/unit/Ver8_unit1_common_tutorial.cpk`.

Their combined selected compressed payload is **750,724 bytes**, excluding tiny ZIP
headers/index traffic. Full multi-gigabyte ZIP downloads are unnecessary. Existing
verified scratch members were reused on this Mac; they are now retained in ignored
`.local/unit-content/sources/`.

The importer validates input SHA-256, length and CRC32 before use. Its read-only
CPK/UTF reader locates the exact `unit_ills_<ID>.png` member. Each output PNG must
match its pinned SHA-256 and pass PNG chunk CRC checks. No raster conversion,
resizing, smoothing or name-based substitution occurs. Original palette transparency
is preserved; the shared SwiftUI image component uses `.interpolation(.none)`.

The source is a **Global-targeted preservation release**, whose build can combine
original cache files, repairs and Memorial-derived recovery. Verified Global ID/name
joins are recorded separately from byte-for-byte retail CDN provenance. Partial ZIP
reads cannot recheck an entire archive's SHA-256; the per-member SHA-256s are pinned
observations from the previous CRC-validated investigation, not publisher-issued
per-file signatures. No supplied IPA is required or read by this importer.

Only tooling, the small lock file and application source belong in Git. Original
metadata, CPKs and PNGs remain under ignored `.local/`, and generated app bundles
stay in DerivedData. A build receipt records content hashes, counts and provenance.

## Reproduce the import

From the repository root:

```sh
cd ~/Documents/Projects/exvius-offline
# Existing verified cache (already prepared on this Mac):
source/ios/.venv/bin/python -B source/ios/content_tools/import_content.py

# Fresh machine/cache: bounded ranges for only five locked members:
source/ios/.venv/bin/python -B source/ios/content_tools/import_content.py --download

# Or reuse an existing verified extraction with static/ and native/ subfolders:
source/ios/.venv/bin/python -B source/ios/content_tools/import_content.py \
  --source-cache /absolute/path/to/global-release-sample
```

The output is `source/ios/.local/unit-content/UnitContent/`:

```text
catalog.json
receipt.json
sprites/100004203.png
sprites/100000102.png
sprites/100000202.png
```

Import is idempotent. It rejects changed/corrupt inputs and refuses to replace a
different existing output. If intentionally revising the lock in a later phase,
preserve the old content folder and produce a new reviewed import. This is unrelated
to campaign storage; do not remove an Application Support save to repair an import.

`--download` explicitly opts into build-time network access. It limits individual
reads, requires the exact Content-Range and filenames, checks the resulting content,
and aborts if the server ignores ranges. It never falls back to a full ZIP download.
If GitHub rate-limits a request, retry later; there is no automatic alternative source.
The Xcode build phase never downloads anything.

## Build and run

The embedded Python runtime must already be prepared as described in
[offline-backend.md](offline-backend.md). Then:

```sh
python3 source/ios/native/generate_project.py

xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase5-Simulator \
  CODE_SIGNING_ALLOWED=NO build

# Unsigned physical arm64 compilation, if signing isn't available:
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase5-Device-Unsigned \
  CODE_SIGNING_ALLOWED=NO build

# Signed physical-device build using the existing local team configuration:
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase5-Device build

open source/ios/native/FFBERevival.xcodeproj
```

Use Xcode's normal DerivedData location or `/private/tmp`, outside synced Documents,
to avoid Finder metadata invalidating signatures. Personal signing settings stay in
ignored `native/Signing.local.xcconfig`.

The default `FFBE_UNIT_CONTENT=preservation` build fails clearly if imported content
is absent/corrupt. For an explicit fixture-only development build, append
`FFBE_UNIT_CONTENT=demo` to xcodebuild. Demo mode keeps the same embedded backend
and saves, and presents labeled fixture names/placeholders. It never silently
substitutes demo content into a preservation build.

## Save preservation and device testing

The normal save path is unchanged:
`Application Support/FFBERevival/offline-demo-v1/campaign.json`.
The catalog never receives that path or modifies stored units. Keep the same app
bundle identifier and install updates over the existing app; **do not uninstall**.

1. Select your iPhone 16 Pro and existing signing team in Xcode, then Run normally.
2. Confirm On-device Python remains selected. Open Collection: starter Rain and
   Lasswell should have real names and sprites if those copies are still owned.
3. Check the last actual summon: names must resolve from its unit IDs; art appears
   only for the three supported IDs. An unillustrated unit must say Art unavailable.
4. Check separate duplicate rows/copy identifiers. Balances and collection size must
   match the existing campaign; this update does not grant units or refill Lapis.
5. Perform an ordinary summon only if you want to spend from your campaign. Confirm
   actual awarded rarity/results. Ludmille's art appears if the actual result is
   `100004203`; other Ludmille forms must not borrow it.
6. Force-close and relaunch; then check again with Airplane Mode and Wi-Fi off. No
   runtime source downloads or external backend should be needed.
7. Optionally switch to HTTP development mode to verify the separate Mac campaign.
   The native image/name lookup remains local in this mode too.

For a deterministic **read-only visual check**, add `--unit-artwork-preview` to the
Xcode scheme's launch arguments. This explicitly labeled verification screen shows
Ludmille, Rain, Lasswell and an unsupported Ludmille form. It is not a summon result,
never initializes the campaign backend, and never grants or modifies units. The
same UnitRowView/UnitArtworkView components render both it and real result/collection
rows. UIKit decoding, SwiftUI image rendering and same-name/different-ID fallback
checks write a diagnostic report under
`Application Support/FFBERevival/validation/unit-artwork-report.json`.
Remove the argument for normal gameplay.

## Tests

```sh
source/ios/.venv/bin/python -B source/ios/tests/test_unit_content.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_service.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_api.py
source/ios/.venv/bin/python -B source/ios/tests/test_offline_entry.py
source/ios/.venv/bin/python -B source/ios/tests/smoke_backend.py
source/ios/.venv/bin/python -B source/ios/tests/test_native_client.py
```

The new content suite uses real pinned inputs, checks all 423 current IDs, known
names/rarities, exact image hashes, corrupt inputs/output, repeatability, legacy-save
bytes and existing transaction behavior. It compiles/runs Swift checks for awarded
versus current-form rarity, PNG decoding, absent-file/unknown-ID fallbacks, same-name
form isolation and duplicate inventory records. Existing probability/guarantee,
rollback, HTTP and no-network suites remain in place.

## Recorded validation for this implementation

- Eight new content tests passed, including real inputs, Swift display models/local
  PNG decoding, corruption rejection, explicit demo mode and old-save compatibility.
- Existing seven summon-service tests, five HTTP API tests and six offline-backend
  tests passed: **26 Python tests in total**, plus the encrypted-backend smoke check
  and actual Swift URLSession contract check.
- Xcode 26.2 Simulator build (arm64/x86_64) and signed physical-device arm64 build passed.
- Simulator artwork screen was visually inspected: three transparent pixel sprites
  and the same-name/different-form missing-art placeholder rendered correctly.
- UIKit decoding and SwiftUI row rendering passed on the actual **iPhone 16 Pro**
  for Ludmille (65×68), Rain (74×59) and Lasswell (71×70).
- The artwork check did not access the campaign. The app was then returned to normal
  offline mode; the existing iPhone campaign was compared with a backup taken before
  the update and was **byte-for-byte unchanged**.
- Simulator real offline summons and terminate/relaunch persistence passed in a
  separate diagnostic campaign. No summons were performed on the existing iPhone
  campaign during validation, and no particular random outcome was forced.
- No Android/gameplay module or existing SummonService implementation was changed.

Physical Airplane Mode/reboot checks remain available in the checklist above; they
were not performed automatically. Only three exact artwork IDs are covered. Remaining
units require further provenance-reviewed imports; they retain real names and honest
missing-art fallbacks now.

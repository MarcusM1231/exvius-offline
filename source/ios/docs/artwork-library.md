# Phase 5C: expanding the offline static sprite library

This phase extends the Phase 5B importer and exact-master-ID catalog. It does not
replace the Python gameplay tables, mutate a campaign, alter banner probabilities,
or add runtime downloads. Existing result/collection components keep nearest-neighbor
scaling and honest missing-art placeholders for unsupported forms.

## Selection and provenance

`content_tools/unit_sources.lock.json` records the 36 common-language unit CPK
locations in `exvius-data-006.zip` and `exvius-data-008.zip`. The earlier 37-package
inventory also included a localized English unit pack in `data-010`; it is not
needed just to look for the current common-language character images.

The discovery tool obtains the current demo IDs and banner base pools through the
existing `demo_data` and `SummonService.details()` implementations in an isolated
temporary planning campaign. It does not change or save the user's campaign. IDs
are prioritized by the existing base weights within each available source. These
weights are not claimed to describe every guaranteed slot's final probability.

Previously inspected CPK tables are reused from ignored local cache. Missing tables
are read by bounded archive ranges: validate the local ZIP filename/header, parse
the CPK header and named TOC, validate file counts/bounds, and record table/index
checksums. Only `unit_ills_<exact master ID>.png` files for current target IDs are
selected. Existing Phase 5B image pins are retained. Different forms are never
matched through a shared name or family.

As before, these are Global-targeted preservation archives, whose content may
include original files, repairs or Memorial-derived recovery. Exact Global ID/name
joins and observed per-image SHA-256s are recorded; that is not a claim of original
retail Global CDN byte provenance for every asset. Full outer ZIP/CPK checksums
cannot be recomputed from small range reads alone.

## Bounded retrieval and manageable batches

```sh
cd ~/Documents/Projects/exvius-offline
# Inspect/import at most 48 additional target IDs, in batches of at most 48:
source/ios/.venv/bin/python -B source/ios/content_tools/expand_artwork.py \
  --batch-size 48 --max-new 48 --budget-mib 16

# Continue toward the complete current dataset:
source/ios/.venv/bin/python -B source/ios/content_tools/expand_artwork.py \
  --batch-size 48 --max-new 423 --budget-mib 16
```

Requests are serial and throttled. A public signed release-CDN URL may be reused
in memory to avoid repeated GitHub redirects; its token is not written into logs
or locks. Each response must be HTTP 206 with the exact Content-Range, total archive
length and body size. Reads are capped at 1 MiB; PNG ranges are coalesced only across
small gaps and within 128 KiB. There is no full-download fallback. A per-run byte
budget limits transfers. HTTP 429 stops the run with Retry-After information rather
than an automatic retry loop. Resume later using the validated cache.

Each selected image must pass exact filename/master-ID checks, PNG signature and
chunk CRCs, bounded decompression and scanline/filter validation. Indexed palette
and alpha pixels are inspected: an unused transparent palette entry is insufficient;
the image must actually contain transparent pixels. Pixel bytes are never resized,
repainted or converted. The SHA-256 is pinned in `content.lock.json` after validation.
Unsupported compressed/interlaced/image formats are not guessed at.

A completed batch publishes an updated content lock and a fully verified immutable
bundle. A failed publication restores the previous lock; previous bundles remain
available. Content-addressed PNGs that were successfully validated can be reused.
If interrupted after lock publication, rerun the importer to finish the corresponding
bundle from its verified cache. The phone's installed bundle is unaffected until
an explicit build/install.

## Rebuild a pinned library without rediscovery

```sh
# Existing cache: verify/reproduce the current pinned catalog and sprites offline.
source/ios/.venv/bin/python -B source/ios/content_tools/import_content.py

# Fresh cache: retrieve only the already-pinned member/image ranges.
source/ios/.venv/bin/python -B source/ios/content_tools/import_content.py --download

python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase5C-Simulator \
  CODE_SIGNING_ALLOWED=NO build

# Use the existing local signing team; do not change the bundle ID or uninstall.
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase5C-Device build
open source/ios/native/FFBERevival.xcodeproj
```

The Xcode build uses the version identified by the exact content-lock checksum.
It does not access the network. Explicit `FFBE_UNIT_CONTENT=demo` builds continue
to work with fixture labels and missing-art placeholders. Embedded Python remains
the default backend; HTTP development mode remains available.

## Coverage and size records

Ignored local reports:

- `.local/unit-content/reports/coverage.json`: demo, banner-union and per-banner
  coverage; exact missing IDs; PNG and content-bundle byte sizes; stop reason.
- `coverage.csv`: every target ID with name, demo/banner membership and artwork status.
- `last-network-run.json`: exact requested ranges, status and received bytes for
  the last invocation. Includes request payload sizes, not TLS/HTTP overhead.
- `.local/unit-content/batches/<lock digest>.json`: validated batch IDs, lock and
  output version, cumulative bytes for that invocation.

PNG bytes and complete content-bundle bytes are reported separately. The content
bundle includes the catalog and receipt; its size increase is compared with the
retained Phase 5B content when available. A measured signed app comparison also
includes code/signature changes, so it is distinct from PNG-only growth.

## Cache layout and backup

All game content remains ignored under `source/ios/.local/unit-content/`:

```text
sources/           five original Phase 5B source members, including decoded metadata
png-cache/         additional validated PNGs addressed by SHA-256
versions/<digest>/UnitContent/   immutable expanded catalogs, PNGs and receipts
UnitContent/       retained Phase 5B three-image bundle, not overwritten
batches/           validation receipts
reports/           coverage and transfer logs
discovery/         inspected CPK file tables
```

To back up the content cache, copy the entire `unit-content` directory, not just
its active version. Also retain the matching source code and the two small lock
files. For example, from the repository root, replacing the destination:

```sh
ditto source/ios/.local/unit-content /Volumes/YOUR_BACKUP/FFBERevival/unit-content
```

Restore it into `source/ios/.local/unit-content/` in a checkout with the matching
`content.lock.json`, then run `import_content.py` to verify it without downloading.
The Python runtime cache is separate and follows the Phase 4 setup instructions.
**This content backup is not a player-save backup.** Application Support campaign
files on the phone remain separate. Do not put either game content or personal saves
into Git. Only tooling, tests, docs and small metadata/checksum locks are source changes.

## Tests and manual device checks

```sh
source/ios/.venv/bin/python -B source/ios/tests/test_artwork_batches.py
source/ios/.venv/bin/python -B source/ios/tests/test_unit_content.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_service.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_api.py
source/ios/.venv/bin/python -B source/ios/tests/test_offline_entry.py
source/ios/.venv/bin/python -B source/ios/tests/smoke_backend.py
source/ios/.venv/bin/python -B source/ios/tests/test_native_client.py
```

Batch tests cover actual transparency, PNG corruption, checksum mismatches, wrong
IDs, cache conflicts, bounded/coalesced requests, ignored ranges/429 behavior,
duplicate and conflicting IDs, failed-publication rollback, offline reproduction,
and unchanged metadata. The existing suites retain save/rollback/guarantee coverage.
Swift/ImageIO checks decode every imported PNG and preserve exact-form fallbacks.

For a read-only visual validation, use Xcode launch argument
`--unit-artwork-preview`. It shows a selection of newly covered forms, the original
three, and an unsupported same-name form. On iOS the diagnostics decode every
imported PNG and render representative rows through SwiftUI without accessing the
campaign. Remove the argument for normal play.

After installing as an update on the iPhone, verify existing currency and collection
size before summoning. Existing stored IDs/results should now have more artwork.
Perform an ordinary summon only if you want to spend from your campaign. Force-close
and relaunch, then check with Airplane Mode and Wi-Fi off. No runtime asset retrieval
should occur. Never uninstall the app or reset the campaign to test new assets.

## Completed Phase 5C validation (2026-11-06)

| Measure | Result |
| --- | ---: |
| Imported static sprites | 423 (420 added to Phase 5B) |
| Demo unit IDs with artwork | 423 / 423 |
| Distinct banner-pool IDs with artwork | 421 / 421 |
| Banner 9100203 | 421 / 421 |
| Banner 49 | 409 / 409 |
| Missing target artwork | 0 |
| Real named catalog IDs | 3,089 of 3,311 master rows |
| PNG payload | 565,399 bytes |
| Complete UnitContent bundle | 1,089,195 bytes |
| UnitContent increase over Phase 5B | 611,036 bytes (596.7 KiB) |
| Signed Debug arm64 app | 39,310,168 bytes |
| Signed app increase over Phase 5B | 719,788 bytes (702.9 KiB) |

Fifteen verified batches used 12 CPK sources from data-006/data-008. Total archive
response bodies were 2,652,898 bytes across 460 bounded requests; no full ZIP or
large CPK was downloaded. The pinned lock SHA-256 is
`1bb958b0dcf6ef4d7a66e34a3e0c1b3f6b412b217ae70b677858f53b21163e1d`.
Coverage is limited to the current demo IDs; the rest of the master catalog retains
missing-art placeholders. This is static artwork, not battle animation coverage.

Passed: batch tests (10), content tests (8), summon-service tests (7), offline-entry
tests (6), HTTP API tests (5), backend smoke test and Swift URLSession development
backend contract. Backend smoke testing explicitly blocked networking. The content
suite reproduced the same locked bundle and tested old-save compatibility. No
Android or gameplay-engine source was modified.

Both Simulator and signed arm64 physical-device builds succeeded with the installed
Xcode toolchain. On Simulator and the connected iPhone 16 Pro, UIKit decoded all
423 bundled images and SwiftUI rendered seven representative rows; an unsupported
same-name form retained its placeholder. Real embedded-Python summons, deductions,
guarantees, collection updates, network rejection and force-quit/relaunch persistence
passed in isolated diagnostic campaigns on both devices.

The first physical diagnostic launch returned CoreDevice error 10004 (no process
identifier); an ordinary launch succeeded and a fresh diagnostic retry passed.
The installed app was updated without uninstalling. The normal campaign was read
before the update and after all diagnostics/normal relaunch; its bytes were identical.
No normal-campaign summon was performed, and no save was restored or overwritten.

Manual checks still required: reboot the phone, enable Airplane Mode with Wi-Fi off,
launch the normal app, and verify collection/results artwork and existing progress.
Automated network guards do not constitute a tested physical radio-off launch or
phone reboot. Run from Xcode with the same bundle ID and signing team; remove
`--unit-artwork-preview` and diagnostic launch arguments for ordinary play.

Changes remain uncommitted. Original images, downloaded source members, cache,
personal signing files, generated apps and player saves remain outside Git.

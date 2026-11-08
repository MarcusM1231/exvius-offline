# Phase 6D-4 — original unit-part animation playback

Implementation date: 8 November 2026. Branch: `ios-port`.

## What changed

The OBTAINED reveal now loops validated exact-master-ID idle frames for four units.
The character still materializes over the same glow, with the existing OBTAINED
artwork, large rarity stars, Continue, Skip All and saved results grid. No name or
numeric-rarity labels were restored. Missing, corrupt or unsupported animations
use the existing exact-ID static sprite. If both are unavailable, the existing
saved-results fallback remains available. The animation has no backend reference.
The crystal entrance, cracking, lighting, Python summoning engine, probabilities,
costs, guarantees, inventory rules, catalog identities and Android code are unchanged.

Developer → Original unit animations provides exact-ID selection, idle/standby,
Play/Pause/Restart, research speed, sequence-frame diagnostics and static comparison.
It needs no campaign and spends nothing. Reduced Motion holds the first frame.

Developer → Personal campaign tools → Add 10,000 free Lapis asks for confirmation,
then explicitly adds and saves free Lapis to the current **offline** campaign.
This is the user's requested personal-build tool, not a summon reward. HTTP mode
is unchanged and the control is disabled there. No Lapis was added to the user's
normal campaign during testing. Cancellation does nothing. Python validates
1–100,000 per operation and a one-billion free-Lapis ceiling; the UI uses 10,000.
The service lock, existing currency helper and existing save method are used, with
in-memory rollback on save failure. Inventory and last-pull data are preserved.
The Swift model prevents overlapping actions and displays the saved backend state.

## Recovered data and provenance

All animation input comes from the Global-targeted preservation release, archive
`exvius-data-008.zip`, container
`native/common_lang/sd/unit/Ver24_unit1_common.cpk`. This is not evidence of
byte-for-byte retail Global CDN provenance. No Memorial/JP or Exvius Reborn assets
were used. Original input bytes are retained unchanged in ignored local storage.

The existing CPK index hash, source bounds and member offsets were reused. Only
16 selected members were needed: sprite sheet, CGG, idle CGS and standby CGS for
each unit. Maria's four cached members were reused; **185,081 bytes** were newly
retrieved in bounded, throttled HTTP 206 requests. No whole archive was downloaded.
The source lock pins stored and CRILAYLA-decoded lengths and SHA-256 identities.
Checksums for newly recovered members pin the first inspected bounded response;
they do not independently verify the full remote ZIP hash without downloading it.
The existing source lock records the preservation archive identity separately.

| Exact master ID | Name/form | Idle records | Standby records | Distinct idle pixel frames |
|---|---|---:|---:|---:|
| 202000203 | Maria | 4 | 4 | 4 |
| 100000103 | Rain, 3★ form | 8 | 4 | 4 |
| 206000103 | Terra | 8 | 4 | 4 |
| 206000113 | Magitek Armor Terra | 16 | 4 | 14 |

The four IDs exist in the current catalog. Rain `100000102` is a different form
and never receives `100000103` animation. Ludmille remains a useful static-fallback
example. The catalog and the 423-unit static-art library were not rewritten.

Eight clips contain 52 sequence records, adding **331,584 bundled bytes** including
metadata and receipts. Maximum decoded pixel storage for one selected clip is
1,468,800 bytes (Magitek Armor Terra idle); Maria idle uses 37,632 bytes. UIKit and
renderer overhead is additional. No global decoded-animation cache exists.

## CGG and CGS findings

Files ending in CSV can still be CRILAYLA-compressed. Validate stored bytes first,
decode with the existing bounded decoder, then verify decoded bytes before parsing.

A selected CGG row has a header and repeated 11-value part records. For this subset,
header anchor is zero; the second value is the exact part count. Each part records
canvas position, flip flags, blend mode, opacity, rotation, texture rectangle and
page. The importer reverses record order before compositing. Forward order visibly
covers Maria's face with back hair; reverse order assembles a coherent character.
Rectangles are explicit atlas regions, not equal cells. Per-part positions and
changing source regions generate the movement; there is no invented limb animation.

The field interpretation and reverse ordering were cross-checked against the
[community assembler's CGG parser](https://github.com/dsxragnarok/ffbetool/blob/main/src/cgg.rs).
This independently corroborates the format interpretation; it is not original
client code or proof of the original summon routing. Implementation here is a
small independent subset, not a bundled third-party renderer.

Supported flips are none, horizontal, vertical or both. Selected rows have zero
rotation and page zero. Other rotations/pages/blends/anchors are explicitly rejected.
Opacity is interpreted as a percentage. Blend zero uses normal source-over;
blend one uses a documented luminous-pixel approximation consistent with the
[community image-processing reference](https://github.com/dsxragnarok/ffbetool/blob/main/src/imageops.rs).
It does not establish original additive GPU semantics. Maria's selected rows use
normal blending; Rain/Terra include mode-one records. These visual approximations
are recorded separately from the original pixel and transform data.

CGS rows reference a CGG row, two canvas offsets and a positive duration value,
consistent with the [community CGS parser](https://github.com/dsxragnarok/ffbetool/blob/main/src/cgs.rs).
Maria idle references rows 0–3, each duration 12; standby references rows 4–7,
each duration 6. Terra deliberately interleaves composition indices. Repeated pixel
frames are retained because sequence ordering and duration still matter.

The player uses the community convention of **60 ticks per second**, not an
assumption that the values are milliseconds. The retail client's timebase has not
been verified. Loops are a playback configuration for idle/standby; the CSV does
not independently prove loop behavior. Unknown records are never silently guessed.
Only selected animation rows are accepted; unselected action rows can contain
unsupported transforms. The research report retains part indices, rectangles,
order, sequence offsets, durations and rendered bounds for inspection.

## Original summon animation assessment

The CPK index includes `atk`, `dead`, `dying`, `idle`, `jump`, `limit_atk`,
`magic_atk`, `magic_standby`, `move`, `standby`, `win_before` and `win` sequences;
Terra also has `limit_atk_before`. This is an inventory, not a claim those actions
have been decoded or should play during acquisition. No specially named acquisition
sequence was found among these units' indexed members.

The earlier original Global layout/reveal research and supplied summon recordings
show the presentation context but do not reliably identify which CGS action is
routed to OBTAINED. The recovered original IPA's executable is encrypted; cached
layouts are not executable routing evidence. The supplied recording is not a
frame-accurate Maria idle/standby reference. **Idle during OBTAINED is an explicit
temporary reconstruction choice**, not a claim of recovered historical routing.
Victory/entrance playback should wait for routing evidence or targeted comparisons.

## Architecture and lifecycle

`unit_animation.py` validates selected part records and sequence references.
`import_unit_animations.py` assembles them at build time with Pillow, using a shared
transparent canvas and union bounds across each clip. Every frame retains the same
origin; per-frame trimming would introduce jitter and is deliberately avoided.
Horizontal anchoring uses the recorded origin; vertical placement keeps that origin
above the existing glow. Nearest-neighbor sampling preserves the original pixels.

`UnitAnimationClip` loads only the current ID/action, checks the pinned source-lock
identity, receipt hashes, file names, frame dimensions/counts, duration bounds and
an eight-MiB decoded-pixel budget. Missing or invalid content returns nil. No
name-based lookup, runtime download or atlas substitution is permitted.

`UnitAnimationView` uses a single UIKit layer with nearest minification and
magnification. Its contents change between already decoded, precomposed original
part frames. There are no per-frame file reads, part assembly or texture creation.
The production reveal uses its existing active-time display link, not a second
animation timer. Each character starts its own playback clock at materialization.
Background suspension freezes the reveal clock; resume discards the wall-clock gap.
Continue releases the old clip before decoding the next. Finish/Skip releases it.
The existing immutable receipt and exactly-once completion continue to govern flow.

The Developer preview has a separate weak-target display link, bounded to 30 Hz.
Pause retains the position; research speed affects elapsed time only. Navigating
away invalidates the link and releases the clip. No second game engine was added.

## Rebuilding

From `/Users/marcusmoore/Documents/Projects/exvius-offline`:

```sh
python3 source/ios/content_tools/recover_unit_animations.py
python3 source/ios/content_tools/import_unit_animations.py
python3 -m unittest discover -s source/ios/tests -p test_unit_animation.py -v
python3 -m unittest discover -s source/ios/tests -p test_offline_entry.py -v
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath /private/tmp/FFBERevival-Phase6D4-Simulator CODE_SIGNING_ALLOWED=NO build
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -derivedDataPath /private/tmp/FFBERevival-Phase6D4-Device build
```

Pillow is needed only for research/import, using a Python environment that has it.
Xcode packaging and runtime do not depend on Pillow. Existing bundled Python,
metadata, UI, static sprites and crystal/reveal resources remain prerequisites.
Content is optional at packaging time; without it, static artwork remains usable.

`--unit-animation-preview` opens the no-campaign interactive preview.
`--unit-animation-diagnostics` runs explicitly labeled render-only fixtures,
including synthetic presentation receipts; these are not summons or awarded units.
`--falling-summon-diagnostics` runs actual isolated embedded-backend transactions.
Add `--character-reveal-reload-check` for zero-summon cold-recovery validation.
`--character-reveal-lab` opens the purple isolated manual summon campaign.
Never use normal campaign summons for automated tests.

Ignored content: `.local/phase6d4` (original research files, previews and journals)
and `.local/unit-animations` (versioned bundle). To preserve it later, copy these
ignored directories to your own external content storage; no backup was created
in this phase. Keep the source locks and tools in Git, not the copyrighted PNGs,
CSV payloads, original IPAs, CPKs, recordings or generated application bundles.

## Validation results

All **94 automated test methods across 16 suites passed**, including strict parser
samples/malformed input, rectangle bounds, transforms, deterministic ordering,
source checksums, reproducible imports, native loop boundaries/pause/speed,
exact-ID coverage, real backend transactions, insufficient currency, save rollback,
HTTP development mode and existing crystal/reveal regressions. The local HTTP
suites were rerun with socket access after the restricted shell blocked their
loopback test servers; their final runs passed. Native clock smoke is included.

Simulator render-only diagnostics passed all eight clips, original-part movement,
OBTAINED, a single and eleven sequential presentation fixtures, static fallback,
Continue, pause/resume, missing-ID/corrupt-receipt rejection and Skip exactly once.
All 40 clip load/release cycles released their weakly observed clip. These tests
exercise resource ownership, not an Instruments leak certification. The recording
shows actual changing sprite-part frames, including moving armor smoke; the player
does not manufacture movement by scaling the whole static sprite.

A separate actual embedded-backend diagnostic used a fresh UUID campaign, performed
exactly two requests/commits (single and eleven), ended at 4,500 Lapis, and verified
saved awards stayed immutable through all reveals. Random draws were not modified
to force an illustrated or animated unit. Synthetic presentation fixtures separately
ensure all supported animation IDs and the static fallback are exercised. Cold
recovery restored the saved eleven awards with **zero** new summon requests.

Simulator build and signed arm64 device build both passed. Strict code-signature
verification passed. An in-place installation to the existing iPhone 16 Pro also
succeeded, preserving `com.example.ffberevival.dev`. **Physical execution was
blocked because iOS reported the device locked.** No physical playback, frame-rate,
Airplane Mode, Home/resume or device thermal claim is made for this phase.
The normal iPhone campaign SHA-256 matched before and after installation:
`6a9f89b6dc79012878694f6a315761025d3632fb672e5ee74c00e4f492cb88a9`.
Temporary read-only checksum copies were deleted; no save backup/restore was made.

No growing decoded-animation cache exists, only one current clip in the controller.
The largest selected clip's raw pixels are about 1.40 MiB, plus UIKit/render costs.
Simulator captures showed coherent part placement and stable origins. Physical
frame pacing, GPU cost and longer memory profiling remain unmeasured. Timings and
mode-one blending remain documented reconstruction choices. Coverage is four of
423 catalog IDs, not universal unit-animation support.

### Tomorrow's iPhone checks

Open the installed app normally and select Developer → Original unit animations.
Try Maria idle/standby, Rain, Terra and Magitek Armor Terra. Compare static/animated,
pause, restart and change speed. Use Home and reopen: playback should resume without
a large time jump and a user-paused preview should remain paused. Repeat in Airplane
Mode with Wi-Fi off, then restore connectivity. Inspect hair, bow, sword and armor
smoke for clipping, jitter or incorrect layering.

For isolated real summons, use the existing Xcode scheme's launch arguments or:

```sh
xcrun devicectl device process launch \
  --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 --terminate-existing \
  com.example.ffberevival.dev --character-reveal-lab
```

Use only the purple test campaign for test spending. Check one and eleven results,
Continue, Skip All, background/resume and offline operation. This lab does not force
supported units; use the no-campaign animation preview to inspect all four examples.
The renderer-only automated route can also be launched with
`--unit-animation-diagnostics` when the phone is unlocked. It does not call Python.

The new Lapis control is intentionally a separate **normal offline campaign**
Developer action: choose Add 10,000 free Lapis, review the confirmation, and accept
only when you want that campaign's balance increased. Check the balance afterward
and after relaunch. It is not invoked by either diagnostic route. Its persistence
and rollback were tested using isolated Python saves; the normal campaign was not
granted currency automatically.

### Remaining work

Verify the four examples on an unlocked physical device before expanding coverage.
Then prioritize exact IDs from the existing banner pools, adding pinned bounded
members incrementally. Validate unfamiliar transforms, pages and blends before
accepting them. Investigate original acquisition routing and timing independently;
do not reinterpret victory or limit animations as summon animation without evidence.
Keep the existing static fallback and immutable transaction/presentation boundary.
No full backup, commit or push was performed. Earlier uncommitted changes and
unrelated `.DS_Store` files were preserved.

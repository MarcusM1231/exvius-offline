# Phase 6D-4B — catalog-driven animation coverage

Branch `ios-port`; implementation and validation started 8 November 2026.

## Scope and provenance

The target is the existing 423-ID demo/summon-art dataset, not every form in the
larger metadata catalog. The current `SummonService.details` pools and demo IDs
were compared against the content lock; they match. Two additional original
Phase 6D-4 research forms are retained, giving 425 gallery rows. Exact IDs alone
select animation. Same-name characters and different rarity forms are not aliases.

Cached indexes identify complete sheet/CGG/idle sets for 420 of the 423 targets.
Starter Rain 100000102, starter Lasswell 100000202 and Ludmille 100004203 have no
complete exact-ID set in these indexes and keep static art. Their other forms are
never substituted. The compressed required-member estimate is about 29.7 MB;
HTTP range coalescing also transfers bounded gaps between nearby members.

Resources are from Global-targeted preservation catalogs in data-006/data-008.
Their presence is not proof of byte-identical retail Global CDN provenance. Source
locks record archive, CPK, payload bounds, pinned index hashes, exact member offsets,
stored/decoded sizes and SHA-256. New member hashes pin the first inspected bounded
response; the complete multi-gigabyte ZIP was not downloaded to recompute its hash.
Original four source identities remain pinned and are checked by regression tests.
No Memorial/JP or third-party revival runtime/resources are introduced here.

## Controlled recovery

`expand_unit_animations.py` plans only target IDs plus preserved research examples.
It chooses the CPK used by existing exact-ID artwork when available, otherwise a
deterministic indexed candidate. The original four keep their original CPK.
An explicit comma-separated `--ids` list can select a smaller reviewed set.
Unknown and duplicate IDs are rejected. A batch contains at most 30 IDs (default 25).

Nearby member reads are coalesced with a maximum 16-KiB gap and one-MiB request.
The client throttles requests and caps the per-batch transfer budget. Exact HTTP
206 Content-Range, source lengths and extraction bounds are required. An ignored
range, rate limit, partial response or checksum mismatch stops processing. There
is no whole-download fallback. A zero-byte connection failure may be retried once;
other failures require reviewing the journal and explicitly resuming. Existing
cached bytes and previously published checksum pins are validated on resume.

`expand_animation_batches.py` repeats controlled batches, reconstructing selected
idle frames after each batch. Unsupported records are reported, not guessed.
Progress, source members, batch receipts and validation reports are in ignored
`.local/phase6d4b`. The small expanded source lock contains no image/CSV payloads.

`import_unit_animations.py` validates the sources, assembles bounded frames,
reports unsupported clips, and generates catalog/coverage/integrity receipts in
versioned ignored `.local/unit-animations`. Idle is recovered for all candidates;
standby is retained for the original four examples. Other action names are inventoried
for future research only. No combat/limit/attack player was added.

## Targeted compatibility change

The existing player and reveal layout are retained. The parser now also accepts
integer quarter-turn rotations (positive counter-clockwise), applied after flips
and before placement. Coordinates remain the part's top-left overlay position.
This matches the [community assembler's processing reference](https://github.com/dsxragnarok/ffbetool/blob/main/src/cgs.rs)
and selected original rows using ±90°. A two-color deterministic pixel test checks
rotation direction and the unchanged origin. Output dimensions are transposed
before checking canvas bounds. Empty trailing CSV padding beyond the declared part count is ignored; interior
missing fields and incorrect record counts still fail. Tests cover both cases.
Arbitrary angles, unknown pages/anchors/blends and
out-of-bounds parts still fail closed. Selected frames retain one union crop and
one origin for the whole clip. Original timing values and sequence order remain
unchanged; the 60-tick timebase and luminous blend approximation remain documented
community/reconstruction choices. Original acquisition routing is still unverified.

## Runtime and gallery

Production still requests exact-ID idle through `UnitAnimationClip`; no manual
per-character Swift mapping is added. One source-lock digest is pinned per content
release. Gallery metadata is checked against the same receipt and digest.
Developer → Original unit animations lists supported and fallback rows, with name/ID
search, target coverage, exact form identity, available actions and fallback reasons.
Open a row for the existing playback, pause, restart, speed and static comparison.
Standby is offered only when packaged, rather than silently selecting a different action.

The current character alone is decoded; there is no global frame cache or preload
of the gallery. Existing active-time clocks, nearest-neighbor rendering, origin
placement, background suspension, Continue, Skip All and immutable result order are
unchanged. Per-clip limits remain 64 frames, 512×512 per frame and eight MiB decoded
pixels. A resource exceeding these limits keeps static fallback. All selected
content is bundled; no runtime request or CGG/CGS parse is introduced.

Python transactions, probabilities, costs, inventory, the explicit Developer Lapis
tool and normal saves are untouched. No Android code, bundle ID, crystal timing,
cracking, lighting, OBTAINED artwork, stars or results layout is changed.

## Reproduce

From `/Users/marcusmoore/Documents/Projects/exvius-offline`, using the existing
Pillow-equipped research Python environment:

```sh
# One reviewed batch, then import; or use the validated repeated-batch runner.
python3 source/ios/content_tools/expand_unit_animations.py --batch-size 25
python3 source/ios/content_tools/expand_animation_batches.py
python3 source/ios/content_tools/import_unit_animations.py
python3 -m unittest discover -s source/ios/tests -p test_animation_expansion.py -v
python3 -m unittest discover -s source/ios/tests -p test_unit_animation.py -v
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

After intentionally publishing a changed content lock, update the one expected-lock
SHA in `UnitAnimationView.swift` before rebuilding. There are no per-ID code edits.
The existing recovery command for the original four remains available and its
source lock is preserved. Prior content versions remain in ignored storage.
No full backup is created. For a later user-managed content backup, copy ignored
`.local/phase6d4`, `.local/phase6d4b` and `.local/unit-animations` to external storage
alongside the source locks. Do not add their copyrighted contents or builds to Git.

## Final coverage and missing-animation explanation

Final validation completed 8 November 2026, including the resumed unlocked-iPhone
session. **417 of 423 target IDs have validated idle playback (98.6%).** The original
four examples are preserved; two are additional research forms outside the target
set, so the bundle contains **419 exact IDs with idle**, plus four standby clips.
That is 423 clips in total, not 423 animated target IDs. There are 2,185 PNG sequence
frames. Repeated original frames and durations are retained.

Six target IDs deliberately use the existing static sprite:

| Exact ID | Unit | Why idle is unavailable |
|---|---|---|
| 100000102 | Starter Rain | No complete exact-ID sheet/CGG/idle set in the inspected indexes. Rain 100000103 is a different form and is not substituted. |
| 100000202 | Starter Lasswell | No complete exact-ID set in the inspected indexes. Another Lasswell form is not substituted. |
| 100004203 | Ludmille | No complete exact-ID set in these indexes; static artwork remains valid. |
| 100013805 | Lila | A selected CGG source rectangle `(953,1144,72,56)` reaches x=1025 in a 1024×1300 sheet. The missing column is not fabricated or silently clipped. |
| 201000104 | Warrior of Light | Idle durations are 22,19,22,0. The zero-duration final record has no validated interpretation in this player; it is not guessed to mean loop, hold or skip. |
| 401001105 | Zargabaath | A selected rectangle `(0,1280,96,104)` lies below the 1280×1280 sheet. No compatible alternate exact-ID set was found in the inspected indexes. |

These are exact-form or data-consistency limitations, not missing unit rewards.
Units, awarded rarity, names, inventory and static artwork remain available. The
reason appears in the gallery. Structural validation and native loading covered the
whole supported library; visual inspection covered representative examples, not a
frame-by-frame historical comparison of every unit.

### Were attack and other animations found?

**Yes. Idle and standby were not the only actions found.** Among the 423 target IDs,
indexed filenames exist for the following actions:

| Indexed action | Target IDs with that filename |
|---|---:|
| Attack (`atk`) | 420 |
| Magic attack (`magic_atk`) | 420 |
| Standby / magic standby | 420 each |
| Victory (`win`) / victory entrance (`win_before`) | 420 each |
| Limit attack (`limit_atk`) | 420 |
| Dying / dead | 420 each |
| Movement (`move`) | 419 |
| Jump | 416 |
| Limit movement (`limit_move`) | 71 |

There are also smaller sets of dance, escape, attack effects, additional attacks,
and action-prefix/transition files. The complete action-name counts are recorded
in the generated investigation artifacts. This is **index availability**, not a
claim that every such sequence contains useful frames or is playable with the
current parser. Filename presence alone does not prove historical routing.

This phase recovered sheets, composition data and **idle** sequences for broad
coverage. **Standby is packaged only for the original four examples**; its absence
from other gallery detail controls means it was not imported in this phase, not
that it is absent from the source archive. Other CGS actions were inventoried but
not downloaded or turned into a combat animation player. Their existing sheets/CGG
can be reused for a future focused attack/victory preview after retrieving and
validating each action's small CGS member. Some actions may reference additional
pages, effects or unsupported transforms. Do not route attacks/victory/limits into
OBTAINED merely because the files exist. Idle remains the intentional default.

## Packaging, validation and performance

- Final animation bundle: **9,737,735 bytes** (about 9.29 MiB), versus 331,584 bytes
  before expansion. Increase: 9,406,151 bytes (about 8.97 MiB).
- Simulator application directory: 77,868,576 bytes versus 68,212,281 bytes before;
  uncompressed increase 9,656,295 bytes (about 9.21 MiB). This is not an exported
  IPA size or App Store download-size estimate.
- Selected original member cache: 29,819,293 bytes. This includes reused original
  examples. Successful-batch receipts record bounded transfer sizes and requests;
  interrupted attempts reused cached bytes and are not fully represented in their
  transfer totals. No complete preservation ZIP/CPK/dataset was downloaded.
- Largest decoded clip: **1,468,800 pixel bytes** (about 1.40 MiB), Magitek Armor
  Terra idle. Maximum per-clip policy remains eight MiB.
- Physical all-clips diagnostic sampled process resident memory at 62,357,504 bytes
  before, 64,929,792 bytes peak and 50,872,320 bytes afterward. These are sampled
  process values including UIKit and renderer overhead, not an Instruments peak or
  GPU-memory profile. Forty weakly observed clip release cycles passed.

All **105 automated tests across 16 suites passed**. Tests cover original four
source and rendered-pixel identity, new coverage, rectangles, rotations, trailing
CSV padding, source checksums, strict/accelerated PNG-validation equivalence,
separate sheet/frame dimension budgets, malformed input, deterministic composition,
loop/pause/speed, restored pinned members, corrupt restore rejection, duplicate IDs,
resumability, bundle bounds, save compatibility and existing summon/HTTP regressions.
PNG chunk CRCs, zlib-length/eof checks, row-filter and palette bounds remain strict.
Animation-only source sheets may reach 4096 pixels (one is 2000×2152); static-art
validation still defaults to 2048, and runtime frames still stop at 512×512.

Simulator and signed arm64 iPhone builds passed, as did strict signature checking.
The iPhone was updated **in place**, never uninstalled. Native diagnostics on both
platforms loaded every one of the 419 idle clips and the original four standby
examples. They also passed Continue, sequential eleven-character fixture reveals,
Skip exactly once, missing/corrupt fallback, pause/resume and resource release.

Separate real embedded-backend diagnostics on both platforms each performed one
single and one eleven-pull in a fresh isolated campaign: exactly two requests and
two commits, ending at 4,500 free Lapis. Saved awards and order stayed immutable
through presentation. Cold recovery on both platforms made zero new summon requests.
No normal-campaign summon, currency grant, reset or save restore was performed.

The normal iPhone save matched the **fresh pre-install checksum from the resumed
session** after all automated tests:
`467389425025172bf642183b9423588806b608de36a80560371bca68892332b6`.
An earlier baseline was retained separately because the user returned later;
we do not treat campaign activity between sessions as a test-induced change.
Temporary checksum copies were deleted. Protected reveal, results, crystal, clock,
Python facade, currency-tool entry and API source hashes remained unchanged.

The user confirmed on the iPhone that sprites look complete, playback/controls
work smoothly, and animations play in Airplane Mode. Automated suspend/resume
passed; a separate user confirmation of the exact Home-while-paused case was not
recorded. Original acquisition routing and retail timing remain unverified.
No full backup, commit or push was performed; earlier uncommitted work is preserved.

## Restoring the ignored cache and device checks

For a future cache restore, retain the pinned discovery indexes under
`.local/unit-content/discovery` as well as the source locks. The original index
recovery tools can rehydrate indexes using bounded reads if necessary. Then run:

```sh
# Restores up to 25 missing units' pinned members per invocation, checking hashes.
# Repeat until restored_members is zero; altered existing files are refused.
python3 source/ios/content_tools/expand_unit_animations.py --restore --batch-size 25 --budget 5000000
python3 source/ios/content_tools/import_unit_animations.py
```

On the installed phone, open Developer → Original unit animations, search a name
or exact master ID, then open the row. Use Play/Pause/Restart, speed and static
comparison; standby appears where packaged. Try Maria, a sword user and a larger
unit. Go Home while paused, reopen without force-closing, and verify it stays paused.
Check offline with Airplane Mode and Wi-Fi off, then restore connectivity.
The gallery has no campaign or Lapis access.

For isolated real summons, launch using the existing Xcode configuration or:

```sh
xcrun devicectl device process launch \
  --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 --terminate-existing \
  com.example.ffberevival.dev --character-reveal-lab
```

Use only the purple test campaign for test spending. Check single/eleven reveals,
Continue, Skip All, Home/resume and offline playback. Normal launch uses the existing
saved campaign and original-style summon flow. Do not uninstall to switch routes.
`--unit-animation-gallery` opens the gallery without loading a campaign;
`--unit-animation-diagnostics` reruns render-only checks. Physical automated
transaction/recovery routes remain the explicit isolated diagnostic flags documented
in Phase 6D-4. Do not reset saves or alter outcomes to force an animated unit.

## Recommended next step

Keep this broad idle library as the reliable summon default. A useful next research
phase is a **small Developer-only attack/victory preview**, recovering only selected
CGS records for already-supported exact IDs and reporting additional dependencies.
Investigate Warrior of Light's zero duration and the two inconsistent texture
references separately. Do not pad, crop, borrow other forms or change award IDs to
increase coverage. Validate each proposed fix against compatible source evidence.

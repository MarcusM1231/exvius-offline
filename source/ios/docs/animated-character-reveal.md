# Phase 6D-2 — animated committed-award character reveals

Implemented on `ios-port`, 2026-11-07. **Simulator only.** No physical-device
build, connection, installation, launch or test was performed. The installed
phone app, bundle ID, Android gameplay, Python rewards, transactions and normal
campaigns were not changed or accessed. Existing uncommitted work is preserved;
no reset, clean, backup, commit or push was performed.

## Result

The production presentation is now:

**Confirm → Python commit/save → one tap-gated crystal → sequential character
reveals → existing saved-results grid.**

A single shows one reveal. An 11-pull shows the eleven immutable awards in backend
order, with one frontend cursor. Each entrance ends at an indefinite **Tap to
Continue** hold. Continue advances one award; Skip/Skip All immediately returns
the entire committed list to the unchanged grid. Crystal Skip still goes directly
to the grid. No character is rerolled, upgraded or awarded by presentation code.

## Original reference and provenance

The YouTube URL `https://www.youtube.com/watch?v=P6tf2Mt6zBM` could not be fetched.
The user then provided the local 21.8-second screen recording:
`/Users/marcusmoore/Downloads/ScreenRecording_11-07-2026 17-48-41_1.mp4`.
It was decoded read-only using macOS AVFoundation. Two-second samples verify
purple cosmos, centered character/light, **OBTAINED below the character**, stars
below, and the general acquisition presentation. Source checksum and sample
contact sheet accompany the report. The recording includes a video's commentary
and subtitles; those are not part of the game's UI. No original keyframes or
exact entrance timing were recovered from it.

The production importer uses the same pinned source members as Phase 6D-1, with
a **separate lock and versioned output**. Source:

- `exvius-data-010.zip`
- `native/en/sd/gacha/Ver2_gachaeffect1.cpk`
- `gacha_result_animation.ssbp` + `gacha_result_animation.png`

Bundled recovered cells: `cosmos`, `getglow`, `get` (OBTAINED), `kirakira`, `glow`,
`glow_4`, `starglow`, `stLight_3/4/5`, `star_0/1/3/4/5`, `star_glow`.
The currently rendered subset is cosmos, getglow, get, kirakira, supported star
families and rarity flares. Some small related cells are bundled for the next
visual-tuning phase but not animated here. Lightning cells, later NV+ artwork,
Memorial textures, third-party resources and Maria's undecoded animation sheet
are **not** used in this production reveal.

These are Global-targeted preservation resources, not proof of byte-identical
original retail Global CDN provenance. The original pixels are retained; static
cells are cropped from validated SS5 v1 rectangles. Composition, placement,
opacity, scaling, blend/pulse settings and entrance timing are reconstructed.
`getglow` remains a probable acquisition glow, not a confirmed solid pedestal.

The importer checks stored and decoded SHA-256s, bounded CRILAYLA decoding, cell
pointers/rectangles, output identity and deterministic receipts. Build packaging
verifies the production lock and optional bundle. Runtime verifies the lock pin,
file set, hashes and PNG decoding. Missing/corrupt optional content leaves the
existing results grid available. No runtime downloads occur.

## Rarity evidence and conservative mapping

`inspect_character_reveal_stars.py` records actual default-cell references in
`gacha_star1..7`, using the already verified SS5 v1 structures. The supported
legacy display is:

| Granted code | Graphic family | Count |
| --- | --- | --- |
| 1–2 | `star_1` (silver) | Actual granted value |
| 3 | `star_3` (blue) | 3 |
| 4 | `star_4` (gold) | 4 |
| 5–6 | `star_5` (rainbow) | Actual granted value |
| Missing/other, including 7/NV ambiguity | Existing numeric/code label | No invented stars |

Default-cell family evidence does not establish the complete original Global
caller or original star movement. The horizontal repeated row is reconstructed.
Blue/gold/rainbow flare selection is a cosmetic reconstruction, never a rarity
upgrade. The earlier-era reference video has visual differences from this
preserved atlas; perfect historical-version fidelity is not claimed.

## Presentation and state machine

`CharacterRevealState` is Foundation-only and contains the immutable
`CommittedSummon`, index, phase, active elapsed time, continuous motion time,
suspension flag and once-only terminal reason. Centralized active-second timing:

| Phase | Duration / exit |
| --- | --- |
| preparing | 0.06 s |
| flash | 0.16 s, fading brief white overlay |
| materializing | 0.65 s, whole-sprite fade/scale |
| obtained | 0.48 s, lettering/stars/name appear |
| waitingForContinue | Indefinite; explicit tap only |
| finished | One terminal callback |

The received tap includes the displayed inventory-instance ID. Taps during
entrance or while suspended are ignored; old-item events cannot act on another
award. Advancing resets the next item's entrance. An actual rapid triple-click
advanced only 1/11 → 2/11 in Simulator. The last Continue completes once.
Skip, missing assets, injected playback failure and interruption share terminal
cleanup; subsequent callbacks/taps do nothing.

`CharacterRevealController` owns a 30 Hz requested display link through a weak
target, frozen catalog display information and the current decoded unit sprite.
It keeps only the current character image, not all eleven. Finish invalidates the
link, clears the callback and releases decoded assets. Backgrounding stops the
link and preserves phase/index/time; resume resets the time origin, so background
time is not consumed. Motion uses a continuous clock rather than a wrapping
visual timeline, preserving the Phase 6C stutter fix. Reduce Motion removes the
whole-sprite scaling/slide; the brief flash and subtle glow remain.

The sprite is looked up by **exact unit master ID**, with the receipt's granted
rarity and real catalog name. Transparent canvas margins are trimmed in memory
only, anchoring visible feet to the glow. Source PNGs and collection components
are unchanged. Nearest-neighbor scaling remains active. No arbitrary CGG/CGS
regions or invented timing units are played. Authentic idle animation can be
added behind this sprite interface later.

`SummonCharacterReveal` provides the cosmic backdrop, glow, centered sprite,
original OBTAINED, supported original stars, exact granted-rarity label, name,
index and Skip/Skip All. `CommittedSummonPresentation` keeps crystal and character
views within the same cover, avoiding a second modal handoff. Both presentation
and character controller identity are bound to the **receipt UUID**. This also
fixes a repeated-cover issue found by the initial diagnostic: SwiftUI could retain
a completed controller during rapid consecutive diagnostic presentations. The
corrected single followed by eleven sequential reveals passed.

## Transaction, recovery and fallback boundary

The Python transaction still commits before the cover appears. `SummonModel`,
receipt validation, offers, probabilities, costs, guarantees, inventory and saves
are unchanged. The reveal component has no backend reference, reward API or save
path. Its cursor is frontend-only and it never modifies the receipt.

The parent's existing `reveal` function still copies `receipt.awards`, checks the
receipt ID and displays the original grid. Completion, Skip and fallback cannot
substitute another list. The grid source matches the existing committed version
byte-for-byte. Collection, banners, balance, confirmation, plain results list,
crystal inspector and research gallery remain present.

If any required UI image or the exact current sprite is unavailable, the sequence
falls back to the complete saved grid, which retains its normal missing-art
placeholder. It does not substitute an image from a same-name unit. Cancellation,
corrupt art and explicit animation failure also return the full award list.

A process kill discards presentation progress, not rewards. Cold launch restores
the existing backend `last_pull`; **View latest saved summon** shows the saved
grid without charging or restarting a summon. No second transaction or new reward
journal was introduced. Resuming the exact reveal index after force termination
is not implemented or required for preserving committed awards.

## Validation actually performed

- **80 automated test methods passed**, suites run in separate processes to avoid
  backend global-state contamination. Includes all earlier backend/content/crystal/
  receipt tests plus five production reveal tests.
- New tests cover immutable 1/11 sequences, deterministic phase boundaries,
  indefinite waiting, invalid deltas, pause/resume, stale/rapid taps, once-only
  completion/Skip/failure, conservative rarity mapping, pinned runtime/import
  manifest agreement, corruption, offline import and no reward/save API in reveal.
- Final generic iOS Simulator build succeeded (arm64/x86_64 compilation). No
  device-targeted xcodebuild command was run.
- A fresh UUID Simulator diagnostic used the **real embedded Python backend**:
  exactly two summon requests and two successful commits, single then eleven. Balances
  were 9,500 and 4,500 from an isolated 10,000 start. Exact IDs/order/rarities/sprites
  and returned full grids were checked. Save SHA-256 before and after each reveal
  matched; no additional backend calls or charges occurred.
- Shared production views/controllers were rendered for flash, materializing,
  obtained, waiting, multi and final-grid captures. Controller-driven taps are
  distinguished from the separate native UI interactions below.
- Missing UI bundle, corrupt PNG/hash, missing exact unit artwork, Skip, injected
  failure and interruption delivered one fallback and cleaned resources. Forty
  repeated resource cycles released images and stopped links. A weak-reference
  check confirmed the display link did not keep a released controller alive.
  This is targeted cleanup evidence, not an Instruments/thermal leak certification.
- Fresh-process isolated reload restored the exact eleven saved awards, unchanged
  save hash and **zero summon requests**.
- Tool-driven native Simulator UI checks exercised real confirmation buttons,
  crystal tap, indefinite waiting, Continue, Home/resume, rapid taps, Skip All,
  single Skip and crystal Skip. Counters count summon operations; state reads are not charges. The four intentionally confirmed transactions
  produced exactly four requests/successes and the expected 3,500 balance.
- API, shared crystal renderer/tap clock, unit catalog/artwork view and Phase 6D-1
  research lock match this phase's starting source hashes. No normal campaign
  file was opened, hashed, copied or reset in this phase. Only named validation
  roots were used. No physical iPhone was accessed.
- Offline evidence: embedded backend and bundled file-only assets, import tests
  forbidding socket use, and no network/reward API in the reveal. Simulator does
  not establish physical Airplane Mode, device frame rate, HDR or battery behavior.

## Files and reproduction

New: `CharacterRevealState.swift`, `SummonCharacterReveal.swift`,
`CharacterRevealDiagnostics.swift`, `CharacterRevealSmoke.swift`,
`character-reveal.lock.json`, `import_character_reveal.py`,
`inspect_character_reveal_stars.py`, `test_character_reveal.py`, this guide.

Focused edits: `SummonInterface.swift` (cover host only),
`SummonCrystalPresentation.swift` (optional shared diagnostic controller injection),
`FFBERevivalApp.swift` / `TapSummonDiagnostics.swift` (explicit isolated launch routes),
`package_python.py` (optional verified reveal bundle), `import_reveal_research.py`
(backward-compatible optional lock argument), generated Xcode project and README.

From `/Users/marcusmoore/Documents/Projects/exvius-offline`:

```sh
python3 source/ios/content_tools/import_character_reveal.py
python3 source/ios/content_tools/inspect_character_reveal_stars.py
python3 -m unittest discover -s source/ios/tests -p test_character_reveal.py -v
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath /private/tmp/FFBERevival-Phase6D2-Simulator \
  CODE_SIGNING_ALLOWED=NO build
xcrun simctl install 64C97F6C-0662-42A7-A57E-37DFBBA13678 \
  /private/tmp/FFBERevival-Phase6D2-Simulator/Build/Products/Debug-iphonesimulator/FFBERevival.app
xcrun simctl launch --terminate-running-process 64C97F6C-0662-42A7-A57E-37DFBBA13678 \
  com.example.ffberevival.dev --character-reveal-lab
```

The UDID above is the existing iPhone 17 Pro **Simulator**, not a physical phone.
If using another Simulator, use its UDID. Existing local Python/unit/UI/crystal
caches remain prerequisites. The production reveal importer uses cached sources
only. Keep original archives and all `.local` content ignored; no asset bytes
were added to Git.

Launch routes:

- `--character-reveal-lab`: fresh isolated 10,000-Lapis campaign; actual production
  banner/confirmation/crystal/reveal/grid controls. Reopening the normal app after
  force-close does not preserve this argument; explicitly relaunch the lab.
- `--character-reveal-diagnostics`: Simulator-only automated shared-component run;
  fresh UUID campaign, captures, counters and saved recovery marker.
- `--character-reveal-reload-check`: separate process, same test campaign, exact
  saved IDs/hash and zero summon requests.
- Existing `--reveal-research-preview`, crystal preview/diagnostic routes and
  Developer navigation remain unchanged. The research gallery was reopened on the
  final Simulator build; the existing Developer crystal diagnostic passed again,
  including all three appearances, pause/restart and stable scene graphs.

## Media, differences and next phase

Ignored diagnostics and media: `source/ios/.local/phase6d2/`. Runtime captures are
also under Application Support `FFBERevival/validation/character-reveal/run-UUID`.
User-facing copies accompany this report. The full 74-second recording shows the
isolated commit-to-crystal-to-character flow, all eleven sequential reveals and
the final grid. A 38-second excerpt is also supplied and stops during the multi
sequence. Confirmation buttons were separately UI-tested, not shown by that
automatic harness. Original
reference frames remain in ignored local storage. Generated media is not committed.

Differences still deliberate: reconstructed entrance timings, whole static sprite
instead of authentic idle, static cosmos rather than decoded scroll, simple light/
sparkle transforms, native name/Continue controls, no unit dialogue/audio/Share
button, modern safe-area composition, and no perfect original BISHAMON or
SpriteStudio animation claim. The supplied video and preserved art may represent
different historical revisions. Small-screen/landscape/VoiceOver polish and long
performance profiling remain Phase 6D-3 work.

For Phase 6D-3, review the images/clip first, then tune scale, glow, entrance pacing,
star placement and reduced-motion/accessibility presentation. Validate genuine
CGG/CGS part composition/time units before adding authentic idle frames. Preserve
this immutable receipt/cursor boundary and full-grid fallback.

**Physical validation remains pending and requires the user's explicit later
approval.** Later checklist: signed build on the same bundle ID without uninstall;
isolated single and eleven; highest-rarity crystal then actual per-award rarity;
Continue/rapid taps/Skip All; Home during each entrance phase and waiting; cold
relaunch saved-grid recovery without charge; Airplane Mode/Wi-Fi off; missing art;
repeat cycles, frame pacing, HDR brightness, memory/thermal/battery checks on the
iPhone 16 Pro. Do not run those device steps as part of Phase 6D-2.

## Later iPhone feedback polish

After explicit device authorization, the signed arm64 app was installed in place.
The user confirmed the reveal, granted star count and Continue flow worked and
reported that stars were too small, name/numeric rarity text was unnecessary,
and the return looked like an iOS sheet. The follow-up enlarges star canvases
from 27 to up to 52 points (fitting all six supported stars), removes visible name
and duplicate numeric rarity for supported star displays, and disables the cover
dismiss animation on completion/Skip. Unsupported rarity codes keep a numeric
fallback; names remain accessible and in collection/results. Receipt/state and
gameplay logic are unchanged. Five focused tests, both builds and the isolated
Simulator runtime diagnostic passed. The update was installed on iPhone without
uninstalling; the normal campaign checksum remained unchanged. Updated visual
confirmation on iPhone is pending.

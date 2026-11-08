# Phase 6D-4C — original summon character action investigation

Research date: 8 November 2026. Branch: `ios-port`. Starting checkpoint:
`d0d1103e5cd949b1e8c9ffecf4d6794eb1b104e7`.

## Finding and confidence

For **the four-star Chizuru shown in the supplied recording**, the strongest visual
match is an **attack → idle → attack** pattern, with an initial ready/idle pose.
Among the requested presets, **C** is the best-supported candidate. This is a
unit-specific visual conclusion, not proof of universal Global routing or recovered
client instructions. Production still uses validated idle exactly as before.

The key discriminator is the return pose: Chizuru holds her katana horizontally
across the waist in the reference, matching idle. Standby carries the blade upward
toward the opposite shoulder; victory holds it down toward the floor. Attack poses
match the observed katana raise and low recovery. Chizuru idle and standby both
contain 48 ticks, so timing alone cannot distinguish presets B and C.

| Confidence | Finding |
|---|---|
| Directly verified | Original files/CGS references, counts, poses, source checksums, six-unit native loading, actual recorded pose changes, finite research playback and tested UI behavior. |
| Strongly supported | Chizuru's reference raise/slash/low recovery resembles `atk`; its return resembles `idle`, not `standby`/`win`. Preset C matches the observed pose families best. |
| Plausible reconstruction | Initial idle followed by recurring attack/idle for this reveal; exact start offset, hold duration, cycle count and use for other units remain unproven. |
| Unsupported as a universal claim | That all Global units use preset C, that Memorial has identical routing, that class names encode the action order, or that a visually similar preview proves executable behavior. |

## Backup gate and production protection

The pre-6D-4C backup completed and passed resource SHA-256, asset receipts, Python
runtime verification and independent Git-bundle recovery before this work began.
The source tree initially had only the two unrelated `.DS_Store` files untracked.
The backup was not modified or recreated. No reset/clean, branch change, uninstall,
save restore, full backup, commit, push or upstream merge was performed here.

Production reveal layout/artwork, stars, crystals, TOUCH SCREEN, source-of-truth
summon service, costs, rates, guarantees, inventory, Lapis tool and original idle
content lock remain byte-identical to the checkpoint. The shared clip loader gains
optional research directory/digest/action arguments; its production defaults still
allow only idle/standby in the existing `UnitAnimations` bundle and use its old pin.
The existing preview display-link driver gains an optional advance callback, nil
for existing clients. No production scene invokes experimental action routing.

## Foundation A — exvius-offline

The backend describes client animation resources but does not implement a native
CGG/CGS OBTAINED action state machine. Relevant existing evidence:

- `source/server/ffbe_config.py` documents `gacha_animation.ssbp` and keys such as
  `gacha_moogle_normal/anime`: banner/SSBP presentation resources, not a unit
  attack/idle sequence.
- `source/server/ffbe_gacha.py:gacha_field_units` documents `BUW0I4JL` motion
  segments and a CGS type for the **paid banner-detail preview**. It cannot be
  treated as the UnitGet/OBTAINED scene's routing.
- `ffbe_gacha.py` references `UnitGetScene::touchEnded` when discussing subsequent
  NV/Vision Card presentation. It does not specify the unit's sprite-action order.
- Android Java/JavaScript bootstrap/display helpers host or control the original
  client/backend; they do not provide a replacement original unit animation engine.

Some comments cite earlier native-client research addresses, but those notes do
not establish the same addresses or routing in the iOS Global 9.1.0 client. No
backend/Android implementation was rewritten or modified.

## Foundation B — original Global IPA

The recovered Global wrapper archive contains a nested ZIP/IPA-style member named
`1078553808`. Archive listings were inspected first; only needed metadata and the
executable bytes were read for static inspection. No executable was run.

- Bundle version: **9.1.0**.
- Executable: `Payload/FF EXVIUS.app/FF EXVIUS`, 39,277,456 bytes.
- Executable SHA-256:
  `5c58c2304dcb1f30e836077871a1749ace9412bbd2076e80aebafda3b34c2021`.
- Mach-O encryption command: `cryptid=1`, offset 32,768, size 29,294,592.

The encrypted executable was not decrypted, bypassed or treated as readable logic.
Recovered gacha CSV anchors/layouts describe presentation positions, not action
calls. Four cached Global CPK indexes had no unit-specific CGG/CGS members matching
the sample filename pattern. No `atk`/`standby`/`win_before`/`magic_atk` routing
literals were found in the inspected decoded gacha layouts. That is a bounded
resource-search result, not proof that the game lacks those actions.

The existing bounded BMB resource reader found reveal-effect texture/model names,
not a decoded character action timeline. No BMB renderer work was added. Layout,
BISHAMON stage effects and CGG/CGS character actions are separate evidence layers.

## Foundation C — Memorial Edition

Static inspection of the separate English-patched Memorial client found:

- Bundle version: **11.1.0**.
- Executable: `Payload/FF EXVIUS.app/FF EXVIUS`, 28,647,024 bytes.
- Executable SHA-256:
  `dad183a035088b3e12eec1941ccbf3f476aa42508d3cdff7eecd28e6b520844d`.
- Mach-O encryption command: `cryptid=0` (no encryption bypass was needed or used).
- Readable RTTI/type strings include `UnitGetScene`, `UnitGetScene::LoopAnimeData`,
  `EdgeAnimeCgs` and action literals `magic_standby` and `win_before`.

These verify retained class/action vocabulary, not the fields of LoopAnimeData,
its action order, whether this scene is active in Memorial mode, or equivalence to
Global. The inspected symbol table did not expose named UnitGetScene methods for
direct action-call analysis. Four cached Memorial CPK indexes likewise contained
no matching sample unit CGG/CGS members; inspected gacha layouts did not expose the
candidate action-routing literals. No Memorial unit pixels or timing records were
substituted into the Global-targeted sample. Memorial/Global evidence stays separate.

## Original gameplay recording

The YouTube URL `https://www.youtube.com/watch?v=P6tf2Mt6zBM` could not be fetched
by the web tool. The supplied local recording was available and was analyzed:

`/Users/marcusmoore/Desktop/Screen Recording 2026-11-08 at 9.53.46 AM.mov`
(the actual filename uses a narrow no-break space before AM; identity is recorded
in the generated JSON). Size 74,303,075 bytes; duration about 21.733 seconds.

Detailed frames were sampled every 0.1 seconds with **zero AVFoundation seek
tolerance**, rather than accepting nearest keyframes. Timestamp ranges below refer
to this local recording, not the YouTube player's original timestamp:

| Approximate local time | Observable pose/behavior |
|---|---|
| 16.6–17.5 s | Chizuru becomes visible with a horizontal ready blade; OBTAINED and four stars are present. |
| 17.6–18.4 s | Lower preparation, then katana raised above/behind the head. |
| 18.5–18.9 s | Bright slash/flash and a low extended-blade recovery pose. |
| 19.0–19.5 s | Return to horizontal ready/idle pose. |
| 19.6–20.1 s | A second raised-blade action begins, then the scene exits. |

The close-up supports repeated attack-like motion separated by idle-looking poses.
It does not establish an infinite loop, initial delay logic, all-unit behavior or
exact action timing. Name/four-star display supports using catalog form 100004604
for this comparison, but the footage does not directly expose its internal master
ID or client build version. No reference was available for each other sample unit's
original acquisition behavior. The contact sheet uses explicit body crops for pose
comparison; the actual player retains every validated part, including atlas effects.

## Recovered action sample and provenance

The exact-ID sample is Maria 202000203, Rain 3★ 100000103, Terra 206000103,
Magitek Armor Terra 206000113, Chizuru 4★ 100004604 and Exdeath 205000703.

All displayed unit action data comes from **Global-targeted preservation**, archive
`exvius-data-008.zip`, with selected members in
`native/common_lang/sd/unit/Ver24_unit1_common.cpk` and
`native/common_lang/sd/unit/Ver39_unit2_common.cpk`. This is not a byte-identical
retail Global CDN claim. Per-unit source keys, archive bounds, pinned index hashes,
member offsets, original stored/decoded checksums and paths are in
`unit-action-research.lock.json`. No same-name or cross-rarity substitution occurs.

Sheets, CGG and already recovered idle/standby records are reused from their pinned
Phase 6D-4B caches. Only missing selected CGS members were requested: **3,524 network
bytes**, using throttled exact HTTP 206 ranges and a 100,000-byte cap. There was no
whole archive download. The isolated sample covers 48 source members. Original
bytes remain unchanged in ignored `.local/phase6d4c/sources`; raw dependency members
remain at their existing ignored locations.

The existing importer—not a second assembler—now accepts optional source-lock,
output, action list and research-report arguments. Its default production output
and receipts remain unchanged. Existing parsing checks rectangle/page/anchor,
rotation, flip, opacity, blend, CGS reference/duration and per-clip memory limits.
Source CGG record order and changing source regions generate the movement.
The new research bundle is about **1,561,686 bytes** and does not replace production.

### Validated action matrix

Numbers are original CGS duration ticks; a dash is an unsupported preview. Tick
values are retained exactly. Seconds in playback use the existing **60-tick research
convention**, not an independently verified Global engine clock.

| Exact ID / unit | idle | standby | atk | magic_atk | win_before | win |
|---|---:|---:|---:|---:|---:|---:|
| 202000203 Maria | 48 | 24 | 117 | 24 | 70 | 40 |
| 100000103 Rain 3★ | 96 | 52 | 71 | 16 | 110 | 48 |
| 206000103 Terra | 64 | 32 | 51 | 16 | 40 | 32 |
| 206000113 Magitek Armor Terra | 192 | 48 | — | 16 | 161 | 48 |
| 100004604 Chizuru 4★ | 48 | 48 | 79 | 24 | 103 | 24 |
| 205000703 Exdeath | 112 | 40 | — | 32 | 78 | 64 |

**34 of 36 requested unit/action combinations** pass current staging and runtime
limits. Exdeath attack positions extend x=-267..96, just beyond the fixed origin's
left boundary (-256). Its full extent is 363×177. Armor Terra attack spans
x=-744..90 (834×181), exceeding the 512-wide staging policy. These are renderer
coverage limits, not claims of corrupt original data. Their attacks and presets
requiring them are disabled; the reason is visible and exact-ID idle/static fallback
remains. No parts were discarded, clamped, translated or invented to force success.

Some effects are sprite-sheet parts and are rendered with the existing normal or
approximate luminous blend. No separate skill/BISHAMON events were inferred from
filenames or synthesized. This is not a full combat-effect renderer. Unknown
external event behavior and original blend semantics remain limitations.

The six target fallback forms from Phase 6D-4B remain unchanged. No source repair,
ID borrowing, rate adjustment or broader action rollout was attempted.

## Developer implementation

Developer → Original unit animations → **Developer action / sequence comparison**
provides exact-ID selection and the six named individual action choices. Only
playable actions/presets are enabled; unsupported reasons remain visible. Existing
idle gallery/search/static comparison and the 417-unit production coverage remain.

Controls include Play, Pause, Restart, Stop, speed (0.25–2×), current action/frame,
static comparison, optional explicit whole-selection repetition and a research
hold (0–2 seconds) between sequence legs. Holds default to zero and repetition is
**off by default**. Finite selections complete once and hold their last frame.
Idle looping in the old gallery is unchanged; this comparison tool does not infer
that attack/victory should loop forever.

All five requested experimental presets are available where their data validates:

- A: idle → idle.
- B: atk → standby → atk → standby.
- C: atk → idle → atk → idle.
- D: win_before → win → idle.
- E: standby → win_before → win.

`UnitActionPlan` advances deterministically only when each action's total duration
(and any explicit hold) ends. It rejects missing/invalid actions rather than skipping
them. Finite final-frame sampling avoids the looping frame clock's return-to-zero
boundary. Completion is once per configured playthrough; restart resets it.
Cancellation releases the clip/plan. The old display-link driver supplies active
elapsed time; no new game engine or parallel animation timer was introduced.

Only the active action's images are decoded. Metadata for the six-unit sample is
small and does not preload textures. Segment transitions release the previous clip
before loading the next. There are no per-frame disk reads or CGG parsing, including
static comparison, which loads once per unit selection. Backgrounding suspends the
clock and preserves explicit pause intent; resume discards elapsed wall time.
Reduced Motion holds the first frame.

A unit-wide fit scale is fixed across actions to preserve anchoring and fit all
validated atlas effects. Body motion can look small for wide attacks. Research zoom
is explicit; values above 1× can crop the camera viewport and are labeled accordingly.
No data is removed from the source or the validated clip.

## Reproduce and inspect

From the repository root, with existing verified caches and Pillow-equipped Python:

```sh
python3 source/ios/content_tools/recover_unit_actions.py
python3 source/ios/content_tools/import_unit_action_research.py
python3 -m unittest discover -s source/ios/tests -p test_unit_actions.py -v
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath /private/tmp/FFBERevival-Phase6D4-Simulator CODE_SIGNING_ALLOWED=NO build
xcrun simctl launch --terminate-running-process \
  64C97F6C-0662-42A7-A57E-37DFBBA13678 com.example.ffberevival.dev --unit-action-preview
```

Use `--unit-action-diagnostics` for render-only automated validation and captures.
It never initializes Python or accesses a campaign. The existing explicitly isolated
`--falling-summon-diagnostics` and `--character-reveal-reload-check` routes remain for
production-flow regressions. Do not run normal-campaign summons for testing.

A signed device build uses `-sdk iphoneos -destination 'generic/platform=iOS'` and
`-derivedDataPath /private/tmp/FFBERevival-Phase6D4-Device`. Update in place with the
same `com.example.ffberevival.dev` identifier and local signing. No uninstall or
campaign reset is needed. Optional research assets missing/corrupt at packaging or
runtime disable research playback and preserve the old production idle/static path.

The raw recording, extracted reference frames, inspected client binary/string data,
recovery journal, source members, reports and converted research bundle all remain
under ignored `.local/phase6d4c`. Only code, metadata locks and documentation belong
in a later authorized source commit. The pre-6D-4C backup remains immutable.

## Validation results and current device limitation

All **111 automated tests in 17 suites passed**, including all prior 105 tests and
six new action-source, coverage, native finite-sequence/clock, zero-duration,
production-protection and no-campaign/API tests. Tests exercise loop boundaries,
explicit repetition/holds, sequence progression, pause/resume, speed, restart,
missing actions and source/receipt integrity. The six new tests were rerun after
the final static-comparison caching change. All 417 production idle IDs and original
sample source/rendering regressions still pass.

Simulator and signed physical-device builds passed. Signature verification passed.
The iPhone app was updated in place with its existing identifier. Simulator and
physical render-only diagnostics both loaded all **34** playable action clips;
the timed Chizuru run exercised all six individual actions and all five presets.
Finite selections stopped on their final frame, completion stayed once-only,
missing actions used exact-ID idle fallback, corrupt receipts were rejected, and
cancellation/background suspension preserved safe state. No campaign was initialized
by this render-only route.

Both platforms passed 40 controller release cycles plus a separate 40-cycle warmed
pass. On the iPhone the warmed resident sample changed from **50,102,272** to
**50,118,656** bytes (+16,384); the sampled all-action peak was 50,118,656 bytes,
with a later end sample 50,135,040 bytes. The first loads/snapshots grew memory from
32,653,312 bytes; this is expected to include image/framework/snapshot allocation.
The stable warmed sample and weak releases are bounded evidence, not an Instruments
leak certification or comprehensive GPU/frame-pacing profile. Source/runtime per-clip
limits remain 64 frames, 512×512 and eight MiB decoded pixels.

The separate real embedded-backend production-flow regression passed on Simulator
and the physical iPhone: single plus eleven, exactly two requests/commits per
platform, immutable awards/order, expected final 4,500 test Lapis, Continue/Skip
and cleanup. Those calls used newly created isolated validation campaigns, never
the normal campaign. Both cold-recovery checks passed with zero new summon calls.
Production continued to display idle during these regressions.

The phone briefly disconnected during the final launch/checksum step, then the
user reconnected it. The final comparison screen launched successfully. The normal
campaign's before/after SHA-256 matches exactly:
`467389425025172bf642183b9423588806b608de36a80560371bca68892332b6`.
Temporary read-only checksum copies were deleted; no save was changed or restored.
Manual visual controls, Home-while-paused and offline checks are awaiting the user's
response; automated physical action/player/regression tests already passed.

For the remaining manual check, use the open `--unit-action-preview` screen. Select Chizuru, enable Experimental sequence,
choose C, and Play. Compare B/D if desired; use explicit research zoom 2–3× for
body inspection (1× fits all atlas effects). Verify Pause, Home/reopen without
force-closing, explicit resume, finite stop, Restart and speed. Repeat offline in
Airplane Mode with Wi-Fi off and restore connectivity. The gallery spends no Lapis.

## Recommended Phase 6D-4D plan — requires review first

1. Review the Chizuru contact sheet and recorded presets. Treat C as a **provisional
   Chizuru-specific choice**, with initial idle handling still a research parameter.
2. Obtain another Global reveal reference before inferring universal behavior or
   adding a broad action mapping. Memorial metadata alone cannot establish it.
3. If approved, start with a small exact-ID opt-in set having complete validated
   attack+idle data. Preserve the existing immutable Python receipt; render actions
   only after commitment. Never reroll, award or spend from the animation layer.
4. Keep source durations and explicitly labeled reconstruction delays; retain
   idle/static and the saved-results grid as failure/cancellation fallbacks.
5. Keep unsupported forms and attacks on existing idle. Investigate Exdeath's
   off-center staging and Armor's wider-than-policy movement separately, without
   silently dropping effects or raising resource limits across the whole library.
6. Validate single/eleven reveals, Skip All, once-only completion, backgrounding,
   offline playback, memory and real save integrity on the phone before rollout.

No Phase 6D-4D production integration, commit or push has been performed.

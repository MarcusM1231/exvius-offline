# Phase 6D-4D — attack recovery and OBTAINED integration

## Evidence and routing decision (before production integration)

The new Desktop recording `Screen Recording 2026-11-08 at 11.36.19 AM.mov`
(narrow no-break space before AM) is 12.1667 seconds long. Exact-time AVFoundation
frames were decoded with both seek tolerances zero. The visible name is Shine,
with four stars. The exact catalog comparison is Shine `100005404`; matching
recovered pixels and the awarded four-star form support this mapping, rather than
name matching alone. The recording does not expose its internal master ID or
client version, so binary source identity is not established by the video.

Observed local recording times: 7.8–8.9 ready stance, 9.0–9.2 crouch,
9.3–9.5 sword raise/ground slash, 9.6–10.0 low recovery, 10.1–10.3 airborne turn,
10.4 descending arc, 10.5–10.7 recovery, 10.8–12.0 ready stance.

Her original `unit_atk_cgs_100005404.csv` has 24 frames, 107 ticks, referencing
CGG rows 44–52 and 56–70. One entire attack already includes multiple ground
swings, the airborne movement and descending slash. At the explicitly provisional
60 ticks/sec this is 1.7833 seconds, consistent with the visible interval.
Multiple visible swings therefore do NOT justify repeating the clip.

The earlier four-star Chizuru reference (comparison `100004604`) shows a complete
raise/slash/recovery and another raised-blade attack, separated by horizontal
ready stance matching idle rather than standby. Its inferred repeat is unit
specific. Neither recording establishes a universal looping rule or exact initial
hold. Default policy: reconstructed 0.8-second initial idle, one complete original
attack, then continuous original idle while waiting for input. Chizuru alone has
an explicit two-attack override with one original idle cycle between attacks.
There is no infinite attack loop. Routing remains configurable in
`ObtainedActionPolicy`; source CGS ticks remain unchanged.

The earlier Global/Memorial/primary-backend investigation remains applicable:
Global 9.1.0 executable is FairPlay encrypted and was not bypassed. Memorial 11.1.0
has readable UnitGetScene/LoopAnimeData/EdgeAnimeCgs names but these do not prove
Global ordering. Backend banner preview motion fields do not define OBTAINED
routing. No Memorial animation pixels are substituted here. See the preceding
`summon-action-investigation.md` and private client-evidence receipts.

## Provenance and recovery

Original animation records are from pinned Global-targeted preservation CPK
indexes in data-006/data-008, not proven byte-for-byte original Global CDN files.
`recover_unit_attacks.py` reuses the expanded idle lock, sheets and CGG records,
and reuses the six-unit research CGS pins. Only missing exact-ID attack CGS members
are retrieved using bounded, throttled HTTP 206 ranges. Each batch saves a source
lock and request journal. A server ignoring ranges or rate limiting stops recovery.
Original source bytes and all outputs live under ignored `.local` storage.
The pre-6D-4C backup is read-only and is not changed.

## Dynamic bounds

Attack-only staging uses the union of original transformed part rectangles and
CGS offsets, with a source-space anchor retained through cropping. Original
relative positions, part order, rotations/flips, alpha and frame ticks are retained.
No effect part is clipped at import time. Attack limits are 2048×1024, 64 sequence
frames and 32 MiB decoded pixels per clip; idle retains its previous 512×512 /
8 MiB limits. Exdeath's source extent is 363×177 (16 frames, 3.92 MiB);
Magitek Armor Terra is 834×181 (32 frames, 18.43 MiB). These require an origin
translation, not invented motion or image downscaling. Unsupported transforms,
missing references or larger clips continue to fall back safely.

Luminous blending is the pre-existing community approximation, not a recovered
original shader. Atlas-local effects are preserved; separate skill/BISHAMON events
are not synthesized or claimed recovered.

## Coverage and retained fallbacks

423 targets: **414 validated attacks**, **413 validated attack+idle pairs**, and
**417 unchanged idles**. Including the two preserved research forms, there are
416 validated attack clips. All 422 indexed attack CGS files were recovered;
425 exact IDs were reviewed (423 targets plus two research forms).

| Exact master ID | Name | Attack limitation |
|---|---|---|
| 100000102 | Rain | No exact-ID animation source set in pinned indexes; static retained. |
| 100000202 | Lasswell | No exact-ID animation source set; static retained. |
| 100004203 | Ludmille | No exact-ID animation source set; static retained. |
| 100013805 | Lila | A referenced source rectangle exceeds sheet width; no guessed crop. |
| 100015805 | Awakened Rain | Original action contains an empty raster frame; current conservative importer rejects it, not a claim of corrupt source. Idle retained. |
| 100019003 | Wayhem | Blend mode 2 is not yet implemented; idle retained. |
| 331000805 | Maria (Xenogears) | 1,056×750 staging ×19 frames = 60,192,000 decoded bytes, above attack budget; idle retained. This is distinct from the supported Maria 202000203. |
| 401001105 | Zargabaath | Referenced source rectangle extends below sheet; static retained. |
| 401002204 | Pirate Jake | CGS structure/duration outside validated subset; idle retained. |

Warrior of Light **201000104** has a validated attack but unsupported idle CGS.
The Developer Attack preview can play it. Production keeps its static fallback
until a safe idle/return path exists; it does not substitute another form.

The full per-ID coverage, source reference and reason are machine-readable in the
bundle's `coverage.json` and the Phase 6D-4D output report. “Unsupported” describes
this renderer/policy, not necessarily bad original data.

## Production implementation and framing

`ObtainedUnitMotion` is owned by the existing `CharacterRevealController`.
It loads only the current exact-ID idle and attack; static art remains available.
`ObtainedActionPolicy` selects finite attack playback and return to continuous
idle, driven by the existing reveal motion time. There is no separate timer,
transaction, network request, award creation or campaign access in this component.
The existing display link, scene suspension, immutable committed receipt,
Continue/Skip All and results-grid handoff remain authoritative.

No per-frame IO occurs. Only current-unit clips are decoded; a normal production
pair is bounded by 8 MiB idle + 32 MiB attack before UIKit overhead. Clips are
released before loading the next award and on cancellation/completion. Reduced
Motion uses the first idle frame. A missing/corrupt attack keeps valid idle; a
missing idle retains the existing static fallback. State changes do not restart
the attack because sampling uses the existing per-award motion-time origin.

The production unit-space anchor stays at the horizontal center. Scale comes
only from the exact-ID idle/standing frame, using the existing body fit and a 3.2×
cap; it remains fixed while attacks play. A wide beam/slash no longer shrinks or
pushes the character to one side. Original attack motion remains relative to that
stable anchor, so intentional leaps/dashes can still move the character.

All original effect pixels remain in the imported clip. Production treats the
screen as a viewport: effects extending beyond it are visibly cut at the screen
edge, as opposed to scaling the entire character down to fit a very long beam.
This is an explicit presentation choice, not source clipping to pass validation.
The Developer toggle “Fit full effects (research)” preserves the full-union view
for inspection and explains why that mode can look small/off-center. Existing
stars, OBTAINED art, glows, crystals and results layout were not redesigned.

Developer → Original unit animations retains name/exact-ID search and now offers
Idle, finite Attack and full OBTAINED preview, static comparison, Pause/Play,
Restart, speed and unsupported reasons. The separate six-unit A–E presets remain.
Warrior of Light's attack is previewable independently of production eligibility.

## Rebuild and recovery

Use the existing Python/Pillow content-tool environment. Preserve `.local` content
privately; do not add it, archives, raw sprites or generated bundles to Git.
The verified pre-6D-4C backup has the original runtime/indices/idle caches but does
not contain these new attack records. Back up new `.local/phase6d4d` and any new
`.local/phase6d4c/sources` separately when the user next requests preservation.
No backup was modified or new full backup created in this phase.

From the repository root, with the existing cache present:

```sh
python3 source/ios/content_tools/recover_unit_attacks.py --all
python3 source/ios/content_tools/import_unit_attacks.py
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

For a checkout missing pinned source members, first restore the private runtime,
content and CPK-index caches using the existing project instructions/backup.
Then use `recover_unit_attacks.py --restore --all` to rehydrate pins using the
existing bounded restore implementation. It rejects changed caches/checksums;
there is no whole-archive fallback. Import again afterward. The build requires
the verified production bundle and fails if it is absent/corrupt; it does not
silently package an incomplete library. Developer research is optional.

For isolated render checks use `--unit-attack-diagnostics`.
For actual Python single/11-pull regression transactions use the existing
`--falling-summon-diagnostics`; it creates a new UUID test campaign.
`--character-reveal-reload-check` verifies the prior isolated run without summoning.
On a physical device also pass `--falling-summon-diagnostics` to satisfy the existing
explicit device-test guard.
Normal campaign currency must never be used for these checks.

Open `source/ios/native/FFBERevival.xcodeproj`, keep the existing local signing team
and `com.example.ffberevival.dev`, select the connected iPhone 16 Pro and Run.
Install/update in place; never delete the app. No network/server is needed at run
time. Manual checks: gallery search Shine and Chizuru, compare Attack/OBTAINED,
pause then Home/return, restart offline in Airplane Mode with Wi-Fi off, restore
connectivity; in the purple isolated summon lab test single, 11-pull, Continue and
Skip All. Verify one committed result set and no second charge.

## Future work

Routing is provisional, not recovered Global native code. Absolute 60 Hz timing,
initial idle hold and a universal repetition rule remain unproven. Shine's single
multi-movement attack and Chizuru's observed repeated action are supported by
visual comparison; swing counts for the other 414 clips were not semantically
annotated. Their full original frame sequences are retained.

Next investigate transparent-frame policy, blend 2, CGS sentinel/duration rules
and multipart/tiled storage for the large Xenogears action before claiming full
coverage. Recover magic/victory/movement using the same action pipeline, exact-ID
pins and finite policies. Limit Bursts may require separate skill/effect events;
CGS filenames alone do not prove complete LB presentation. Do not guess missing
source pixels or claim complete original shader/BISHAMON recovery.

## Automated validation commands

Run each unittest module in a fresh process. The original backend binds its data
root at import time and intentionally rejects switching fixture roots within one
process; one global `unittest discover` run therefore produces cross-suite errors.
The 17 isolated modules contain 119 tests. The first combined-process attempt is
retained in the investigation outputs instead of being hidden.

```sh
for suite in source/ios/tests/test_*.py; do
  python3 -m unittest discover -s source/ios/tests -p "$(basename "$suite")" -v || break
done
python3 source/ios/tests/test_native_client.py
source/ios/.venv/bin/python source/ios/tests/smoke_backend.py
```

Content-tool imports were validated with Python 3.9 / Pillow 9.1.1; the standalone
backend smoke uses the existing Python 3.12 environment with cryptography/PyYAML.
No dependency changes were required in the embedded iOS Python backend.

The first render-only Simulator run loaded the library but timed out on an
initially paused reveal. The harness now explicitly starts its fixture clock once
the production view has begun. Production lifecycle behavior was not changed to
work around a test fixture. The successful rerun decoded all 416 attacks and
covered Maria, Rain 3-star, Terra, Magitek Armor Terra, Chizuru, Exdeath, Shine,
a 270-tick long action (213000504), and exact-ID static fallback Rain 100000102.

The existing 30 Hz display link is retained; the source timeline still uses its
unchanged ticks at the provisional 60-tick timebase. Very short one-tick source
frames may be temporally sampled out at normal speed. Slow playback in the
Developer gallery permits closer inspection. No promise of every original frame
being presented at native 60 Hz or exact historical frame pacing is made.

## Final automated validation results

The centered correction was rebuilt for Simulator and signed physical iPhone,
then tested on both. Both native scans decoded all **416 attacks**. Nine production
reveal fixtures passed, including source-wide Magitek Armor Terra and Exdeath,
Shine/Chizuru, long 270-tick action and exact-ID static fallback. Runtime checks
verified a centered anchor and idle-based scale at 320/402/768-point widths.
The earlier full-effect-fit captures are retained as historical attempts; final
captures are explicitly labeled **Centered**.

Both final actual-gameplay regression runs passed in fresh isolated UUID campaigns:
one single plus one eleven-pull, two requests/two commits per run, correct costs,
immutable awarded IDs/rarities/order, no save writes during reveals, exactly-once
completion, cleanup, Skip/failure/missing-art fallback. Both cold-relaunch checks
returned the same 11 awards with **zero new requests**, preserving the test save.
These repeat runs were deliberate tests in separate campaigns, not duplicate
summons or charges in one campaign. No normal-campaign currency was spent.

All **119 tests in 17 fresh-process unittest suites** passed before the framing
correction; the finite-routing/body-framing smoke was rerun afterward and passed.
Both final native renderer/regression runs validate the corrected code. The Swift
HTTP development contract and original Python backend smoke also passed. Full
logs and machine-readable receipts accompany the investigation report.

| Measurement | Simulator | iPhone 16 Pro |
|---|---:|---:|
| Library-scan sampled resident peak | 154,857,472 bytes | 60,604,416 bytes |
| Warm-cycle resident before | 178,909,184 bytes | 73,695,232 bytes |
| Warm-cycle resident after | 179,187,712 bytes | 63,995,904 bytes |
| Released motion owners | 40 / 40 | 40 / 40 |
| Largest decoded attack in bundle | 15,993,600 bytes | 15,993,600 bytes |

These are sampled process counters, not Instruments/GPU peak measurements or a
universal leak-free/FPS guarantee. The largest final decoded clip is smaller than
the conservative import staging limit because transparent outer canvas is trimmed
once per action, preserving its original anchor and relative motion.

The production bundle is **51,066,000 bytes**, up
**41,328,265 bytes** from the prior idle library. Final
signed device app is **103,151,376 bytes**; Simulator app is
**122,328,431 bytes**. These are logical file bytes, not IPA
compression or OS installation totals. Optional validation runs also write
screenshots/reports under the app's separate validation directory.

Normal iPhone campaign before/after SHA-256 after the final build and tests:
`467389425025172bf642183b9423588806b608de36a80560371bca68892332b6` — identical. Only temporary read-only copies were hashed,
then removed; no restore/reset/write occurred. The app was updated in place using
`com.example.ffberevival.dev`. Wi-Fi interruptions required retrying the update;
there was no uninstall. The verified resource backup remains untouched.

Manual visual, Pause/Home and Airplane Mode feedback is recorded separately in
the Phase 6D-4D report. Preserve the current uncommitted Phase 6D-4C/4D source and
new private caches before future work; no commit, push or new full backup was made.


Final physical-device manual feedback: the corrected previews “look great”; after
Pause → Home → reopen they “Stayed paused until Play”; in Airplane Mode with
Wi-Fi off the user confirmed “it finishes attack.” These statements record the
scope of the user's confirmation. Finite return-to-idle was also verified by the
automated final native/policy checks. No additional campaign transaction was
performed for these Developer gallery checks.

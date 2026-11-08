# Phase 6D-3A — falling crystal entrance and recovered prompt

Implemented on `ios-port`, preserving all earlier uncommitted work. No Android,
Python reward/currency/inventory/save logic or bundle-ID change. No uninstall,
normal-campaign summon, full backup, commit or push.

## Reference and recovered evidence

The earlier recording and the corrected new recording at
`/Users/marcusmoore/Desktop/FFBE Revive/phase6d/ScreenRecording_11-07-2026 23-01-57_1.mp4`
were inspected through extracted frames. The new clip is about 30.97 seconds.
It shows a staggered mixed-color crystal stream against a cloudy corridor, varied
sizes/depth, then a main crystal. Cropping, video edits, player controls and taps
prevent an exact total-count/timing inference. Paths, count, interpolation,
lighting and camera-space staging below are reconstructed, not recovered BMB
keyframes. The later character-reveal screenshot is retained as a future visual
reference; this phase intentionally leaves the approved character reveal intact.

The cloud/geometry were already cached. A final cross-check recovered **one
10,454-byte PNG** by an exact HTTP 206 range from an existing pinned index; no
full ZIP/CPK was downloaded:

| Resource | Source | Verification / interpretation |
| --- | --- | --- |
| `touchscreen.png`, 256×256 (selected) | `exvius-data-002.zip`, `native/common_lang/sd/effectResource/Ver13_effectResource1_common.cpk` | Exact original preserved **TOUCH SCREEN** pixels; source index/TOC, member bounds, PNG integrity and hashes validated. |
| English `touchscreen.png` (research alternative only) | `exvius-data-010.zip`, `native/en/sd/gacha/Ver2_gachaeffect1.cpk` | Reads **Tap Screen**; retained unchanged in the old cache and superseded for this presentation by the shared classic wording. |
| `gacha_tapscreen_text.bmb` | Existing Phase 6A `Ver31_gachaeffect1_common` cache | Bounded decoded name table references `touchscreen`; the effect timeline is not decoded. |
| `deff_cloud_002.png`, 256×256 | `exvius-data-003.zip`, `native/common_lang/sd/gacha/Ver31_gachaeffect1_common.cpk` | Original preserved cloud pixels; gacha effect reference tables mention this dependency. Our scrolling plane is a reconstruction, not the original cloud-corridor shader. |
| Models 001/002, original crystal/caustic/prismatic/glow textures | Existing verified Phase 6C reconstruction bundle | Reused without changing geometry, UVs or winding. No second model parser/runtime. |

`gacha_n1_c1`, `gacha_r1_c1` and `gacha_base_002_c1` name tables were inspected.
They contain mother-crystal/cloud/glow dependencies, but do not establish decoded
falling trajectories. Existing original Global layout findings, preservation
indexes and third-party PCK name matches were reviewed; no Memorial/JP texture,
third-party renderer, executable or proprietary source was incorporated.
Global-targeted preservation provenance does not prove retail Global CDN byte
identity. The machine inventory records source paths, hashes and archive joins.

## One shared crystal timeline

`TapSummonClock` now supports:

**fallingCrystals → arriving → waitingForTap → opening → revealing → finished**

- Falling: **3.2 active seconds**. Seven passing nodes clone the existing original
  layered crystal geometry/material pipeline, with deterministic staggered paths,
  depth, scale and subtle rotation. At the user's reference-based request, falling
  crystals use a 1.25× horizontal X/Z presentation scale; this blends back to
  1.0× during the main arrival, leaving the settled model and original mesh bytes
  unchanged. Original glow textures form their trails.
- During the last **0.55 s** of that phase, the **existing main crystal node** enters
  from above. It fades to 0.45 opacity and reaches the legacy arrival's starting
  position/scale. There is no second hero mesh or hard-cut replacement.
- Main arrival: existing **0.9 s** settling/growing pose, with continuous opacity
  and motion. The original cloud plane fades away before the main presentation.
- Waiting: indefinite. Recovered prompt appears only here; it pulses using the
  same continuous motion clock. Early taps are ignored and are not buffered.
- One valid tap hides the prompt and starts existing **1.2 s opening + 0.4 s reveal
  handoff**. Repeated taps cannot reopen it. Breaking/shard behavior is unchanged.

Constants and seven path/scale presets live in `CrystalEntrance.swift` for tuning.
The configured eight visual entrants mean seven background crystals and one main
crystal, **not eight awarded units**. Background blue/gold/rainbow colors are
purely decorative, matching the observed mix. Only the main crystal follows the
existing receipt-derived cosmetic rarity mapping. None of these choices changes
an award, count, granted rarity, cost or guarantee.

SceneKit nodes are allocated once per scene build; no per-frame mesh creation,
SCNAction timeline or additional timer was added. The existing display link advances
the existing tap clock. The prior continuous-idle-motion stutter fix is retained.
Stop/cancel hides all passing nodes and invalidates playback. Rebuild clears
previous passing nodes, preventing scene-graph growth.

## Prompt and fallback

`CrystalTouchPrompt` overlays the recovered shared **TOUCH SCREEN** graphic near
the viewport's lower edge only when `showsTouchPrompt` is true. Accessibility
labels it TOUCH SCREEN. Both same-basename source variants were visually inspected;
filename equality alone was not used as compatibility evidence. The original
retail client's locale-override selection remains unproven. It never appears during falling, arrival or opening and
hides on the first accepted tap. Original pixels are not relabeled or repainted.

If the optional prompt/cloud bundle is missing or corrupt, the renderer retains
its original crystal geometry and uses clearly reconstructed serif **TOUCH SCREEN**
text and the dark background. If core crystal resources fail, the existing
committed-award fallback returns to the saved grid. No runtime downloads occur.

`import_crystal_entrance.py` checks exact cached SHA-256s, PNG integrity/transparency
and output identity. It refuses to overwrite changed output artwork. Xcode verifies
the small optional bundle before packaging; runtime checks the lock pin, file set,
hashes and image decoding. The two source textures are 256×256 each (about 0.5 MiB
combined decoded RGBA pixels, excluding mipmaps/buffers). Original cached files
and all copyrighted derivatives remain ignored.

## Production boundary and lifecycle

Production still constructs the cover only from a successfully correlated,
immutable committed receipt. One backend transaction precedes one entrance/main
crystal; eleven awards then pass through the existing frontend reveal cursor.
The falling renderer has no backend or save reference. Skip during any entrance
stage returns the full committed award list. The existing grid, cold last-pull
recovery, duplicate protections and approved reveal polish remain intact.

Pause/background suspends the same clock and display link. Resume resets the
frame-time origin and continues the same phase/position; background time does not
advance falling or open the crystal. Waiting remains tap-gated after returning.
Process termination uses existing saved-award recovery, not another paid request.

## Developer tools

**Developer → Inspect original crystal mesh → Open animated crystal reconstruction**.
The original static/automatic demo controls remain available. New controls:

- Play / Restart entrance.
- Pause and Resume entrance.
- Blue / Gold / Rainbow selection.
- Inspect TOUCH SCREEN (static waiting inspection).
- Open manually (resume if needed, then apply one valid tap).
- Compare old tap arrival (no falling phase).
- Stop and existing layer/model/speed inspection.

These tools are render-only: no backend, currency, inventory or campaign access.
The legacy automatic demo remains distinct from the production tap-gated path.

## Isolation and build commands

From `/Users/marcusmoore/Documents/Projects/exvius-offline`:

```sh
python3 source/ios/content_tools/recover_crystal_entrance.py
python3 source/ios/content_tools/import_crystal_entrance.py
python3 -m unittest discover -s source/ios/tests -p test_crystal_entrance.py -v
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath /private/tmp/FFBERevival-Phase6D3A-Simulator CODE_SIGNING_ALLOWED=NO build
xcrun simctl install 64C97F6C-0662-42A7-A57E-37DFBBA13678 \
  /private/tmp/FFBERevival-Phase6D3A-Simulator/Build/Products/Debug-iphonesimulator/FFBERevival.app
xcrun simctl launch --terminate-running-process 64C97F6C-0662-42A7-A57E-37DFBBA13678 \
  com.example.ffberevival.dev --falling-summon-diagnostics
```

The UDID above is the existing iPhone 17 Pro **Simulator**. Existing local runtime,
unit, UI and reconstruction content remain prerequisites. Launch-only diagnostics
bypass `ContentView` and normal campaign initialization:

- `--falling-crystal-diagnostics`: render-only blue/gold/rainbow, entrance snapshots,
  pause/tap/fallback checks, node/display-link/repeated-cycle diagnostics.
- `--falling-summon-diagnostics`: actual embedded Python, fresh UUID validation
  campaign, one single + eleven, shared production views/controllers and captures.
  Scripted test taps are not an automatic-break behavior in production.
- Add `--character-reveal-reload-check` to the preceding route for a separate
  process restoring its exact saved awards/hash with zero summon requests.
- `--character-reveal-lab`: fresh purple test campaign for real touch/Home/offline
  checks. Force-close does not preserve launch flags; explicitly relaunch the lab.

The old `--character-reveal-diagnostics` route remains Simulator-only on its own;
physical execution requires the explicitly authorized `--falling-summon-diagnostics`
flag. All new writable test content lives under Application Support
`FFBERevival/validation`, never the normal campaign or read-only application bundle.
Ignored local research/media lives in `source/ios/.local/phase6d3a` and optional
bundles in `.local/crystal-entrance`. No backup was created.

## Known differences and Phase 6D-3B

This is a recognizable reconstruction, not complete original animation recovery.
The cloud background is a moving plane rather than a recovered 3D swirling tunnel;
trajectory count/depth, timing, scales, glow strength and prompt placement are
reconstructed. The English Tap Screen alternative is not silently substituted for the selected
shared TOUCH SCREEN artwork. Exact original locale/version selection remains unknown. Character idle frames, original audio/keyframe timing and new crack/shard
work were not added here.

For Phase 6D-3B: review the new clips first, then improve crack lines, fragment
silhouettes and light-burst pacing using verified geometry/texture dependencies.
Keep the tap gate, immutable receipt, exactly-once completion and full-grid fallback.
Do not label model003 as original shards without evidence. The later supplied
reveal screenshot's smaller character/large rarity shine is a separate recorded
visual target; avoid coupling it to reward generation or changing star counts.


## Final validation — 8 November 2026

All 85 automated test methods passed across 14 suites. Simulator and signed arm64
iPhone builds succeeded; strict code-signature verification passed. Both platforms
completed real embedded-backend single and eleven-pull diagnostics in fresh isolated
validation campaigns: exactly two backend requests and commits, with unchanged saved
awards throughout presentation. Cold recovery performed zero summon requests.

The connected iPhone 16 Pro passed blue/gold/rainbow rendering, early/repeated tap
rejection, indefinite waiting, pause/resume, missing/corrupt optional-resource
fallback, missing-core fallback and 40 repeated playback cycles. Scene node count
remained 89 and the controller released. Measured display-link intervals were
16.669 ms median and p95; these are callback measurements, not GPU profiling.
Warm resident memory changed from 67,846,144 to 69,582,848 bytes across repeated
cycles. This is a bounded diagnostic, not an Instruments leak certification.

The user confirmed the wider falling crystals run nicely, Home/resume works, and
an Airplane Mode eleven-pull with Skip All still works. Falling width is 1.25 times
the previous width, blending back to the unchanged settled main crystal.
Normal campaign checksums matched before and after automated device validation.
No normal campaign was used for test transactions. No uninstall, campaign restore,
backup, Git commit or push was performed. Existing unrelated changes remain intact.

### Physical-device rebuild and testing

With the existing signing configuration and paired phone unlocked:

```sh
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -derivedDataPath /private/tmp/FFBERevival-Phase6D3A-Device build
xcrun devicectl device install app --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 \
  /private/tmp/FFBERevival-Phase6D3A-Device/Build/Products/Debug-iphoneos/FFBERevival.app
xcrun devicectl device process launch --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 \
  com.example.ffberevival.dev --character-reveal-lab
```

This updates the existing bundle in place. Never uninstall it to resolve a build
issue. Use the purple isolated campaign for spending tests. Check single and
11-pulls, wait without tapping, use Home and resume, tap once, and try Skip All.
Repeat offline with Airplane Mode and Wi-Fi off, then restore connectivity.
Launch flags are not retained after force-closing; explicitly relaunch the lab.

### Files introduced for this entrance

- `native/FFBERevival/CrystalEntrance.swift`: deterministic entrance timing and poses.
- `native/FFBERevival/CrystalEntranceResources.swift`: verified resources and prompt.
- `native/FFBERevival/CrystalEntranceDiagnostics.swift`: isolated renderer checks.
- `content_tools/crystal-entrance.lock.json` and `crystal-entrance-source.lock.json`:
  small content/source identities, without copyrighted payloads.
- `content_tools/import_crystal_entrance.py` and `recover_crystal_entrance.py`:
  validated packaging and bounded recovery.
- `native/tests/CrystalEntranceSmoke.swift` and `tests/test_crystal_entrance.py`:
  state, geometry trajectory and content validation checks.

Existing crystal controller, tap state, presentation, diagnostics, packaging and
project generation were extended. The accepted character reveal, results mapping,
backend transactions and Android gameplay were preserved.

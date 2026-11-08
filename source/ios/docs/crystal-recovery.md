# Phase 6C-1 — original crystal geometry recovery

**Result: an original mother-crystal mesh is recovered and inspectable on iOS.
Original crystal animation playback is not recovered.** The Developer tab has an
isolated SceneKit inspector. Production summons still go directly to the Phase 6B
results screen. There is no invented drop, break, blue tint, upgrade or timing.

The project remained on `ios-port`, starting from `8b8e32d`. Initially only two
`.DS_Store` files were untracked; they were left alone. Python gameplay, rates,
transactions, inventory, unit content and production summon presentation were not
modified. New cache files are separate from Phase 5C, Phase 6A and Phase 6B content.

## What was actually recovered

The minimal packaged visual uses these preservation resources:

- `exvius-data-002.zip` →
  `native/common_lang/sd/effectResource/Ver4_effectResource1_common_tutorial.cpk`
  → `model_mothercrystal_001.m3r` and `deff_mothercrystal_001.png`.
- Model: 960 stored vertices, 320 triangles, 162 distinct positions, normals, UVs
  and packed per-vertex attribute words. The original texture is 128×128 grayscale.
- The decoded model contains the matching texture basename
  `deff_mothercrystal_001`; no name/family/rarity substitution is used.

The inspector preserves source geometry, indices, normals, UVs, texture bytes and
raw packed attributes. Its orthographic camera, Lambert lighting, double-sided
material and conventional normalized RGBA interpretation of packed attributes are
**diagnostic choices**, not a recovered BISHAMON shader/material setup. The packed
values vary and must not be mistaken for padding or interpreted as floating-point
NaNs. Their exact original shader semantics remain unverified.

The visible crystal shape is game data, not newly drawn geometry. Its final color,
transparency, highlights, projection and motion are not claimed to match the original
summon presentation. The texture itself is grayscale; no guessed blue color is applied.

## Renderer identification and source separation

The unencrypted **English-patched Memorial** client contains symbols for
`ml::bm::ParticleEmitterNode`, `bmb::param::Model`, `QuadTraits`, `StripeTraits`,
particle variants, translation/UV curve modules and BISHAMON-related wrappers.
Selected file name tables include `D:/bishamon_lib/`. This identifies the middleware
family, rather than assuming `.bmb` is video or a SpriteStudio file.

MATCHLOCK's own [BISHAMON overview](https://www.matchlock.co.jp/manual/bishamon%E3%83%84%E3%83%BC%E3%83%AB%E3%82%AA%E3%83%B3%E3%83%A9%E3%82%A4%E3%83%B3%E3%83%9E%E3%83%8B%E3%83%A5%E3%82%A2%E3%83%AB/overview/summary/)
describes an emitter/node-tree effect system. Its
[SDK integration seminar](https://www.matchlock.co.jp/seminar/GES01_03.pdf)
separately describes managing BMB, model and texture resources. These support the
architecture identification; they do not provide the binary field specification
needed for this particular game's complete renderer.

The original Global IPA and Memorial both contain
`Payload/FF EXVIUS.app/bishamon/bmshaderpack.bin`, 777,024 bytes, with identical
SHA-256 `2f36d1839cad4ede93764b4237a05d4cbe4085392a9a2b6f93c5833e14d7dd0b`.
Memorial additionally has `bmshaderpack_gl2.bin`, 687,408 bytes, with a different
hash. These were read and retained as provenance evidence, **not integrated into
the app or executed**. Byte equality of one shader pack does not establish that
all Global/Memorial code, effect versions or game IDs are interchangeable.

The Global executable still has an encrypted code region, so the available
Memorial symbols are explicitly comparative evidence. Selected Memorial entry points
also contain Frida trampolines; their hook code must not be mistaken for original
renderer behavior. No client binary was modified, loaded or patched by this phase.

No `.bmb`/`.m3r` player or loader implementation was found in repository source.
Existing code concerns CPK/CRILAYLA, static images, backend effect-pattern selection
and SpriteStudio metadata. None implements the BISHAMON node/particle renderer.

## Verified file structure: IBMB

The new bounded probe is `content_tools/crystal_formats.py`. These statements are
observed byte layouts, not a complete published specification:

| Offset | Verified observation |
| --- | --- |
| `0x00` | ASCII `IBMB` |
| `0x04` | Raw tag `0x00000051` in inspected `gacha_crystal_n1/r1` files; `0x01030101` in the EX16 samples |
| `0x08` | Raw word `0x41` in these samples |
| `0x10`, `0x14` | Raw counts 8 / 3 for the inspected crystal c1 files; 7 / 5 for blue/gold EX16. Meanings not fully established |
| `0x48`, `0x50` | Both contain 329 in the crystal c1 samples. Not assumed to be a frame count, duration or fps |
| `0x58`, `0x5c` | In these samples, delimit a printable null-terminated name region followed by `0xba` padding |

The probe validates signature, minimum header length, region bounds, null termination,
ASCII content and observed padding. It records every raw header word. It deliberately
does not label unknown words as official format versions, node types or timing.

The name region of `gacha_crystal_n1_c1.bmb` is `[0x6380,0x6430)`. It contains
`../`, then these literal dependency symbols:

```text
model_glow_001              glow_001
lightburst_011              model_mothercrystal_001
deff_mothercrystal_001      glow_013
model_mothercrystal_002     deffuse_soccerball_001
glow_003                   glow_008
star_003
```

All eleven literal symbols have actual retrieved matching files in the Phase 6A/new
preservation caches. That is **not** proof that every runtime override/binding is
resolved. For example `model_mothercrystal_002.m3r` internally names
`deffuse_cloud_001`, while the BMB table also names `deffuse_soccerball_001`.
The former PNG appears in the shared package TOC but was not fetched for this
prototype; the override relationship is unverified. Model 001 and its directly
matching texture avoid this ambiguity for the minimal inspector.

### Important EX16 correction

The actual files were verified from the Phase 6A inventory:

```text
exvius-data-003.zip
native/common_lang/sd/gacha/Ver31_gachaeffect1_common.cpk
  EX16_2openblue.bmb
  EX16_2opengold.bmb
  EX16_2openraindow.bmb       # exact stored typo
  gacha_crystal_n1_c1.bmb
  gacha_crystal_r1_c1.bmb
```

The EX16 files reference `EX16_chesttop`, `EX16_chestlock`, `EX16_chestbot`,
`EX16_expbox`, chest glow and related assets. They are not established as the normal
mother-crystal breaking sequence just because their names say “openblue”. Relevant
chest candidates also exist in the shared SG resource TOC. They were not bundled or
substituted for the crystal. `D:/bishamon_lib/` is an exported path string, not a
request to find that drive on the Mac or fetch an unrelated library.

### Color and rarity findings

The inspected n1/r1 c1 binaries have the same length/header and differ at 21
32-bit words. Several changes look like RGB triplets, including:

| Offset | n1 floating-point candidates | r1 floating-point candidates |
| --- | --- | --- |
| `0x31d0` | approximately (0, 0.6465, 1) | (1, 0.7959, 0.2221) |
| `0x48b0` | (0.6286, 0.8600, 1) | (1, 0.9170, 0.5134) |

These are strong color-parameter candidates, **not verified material assignments**.
Their owning nodes, blending and interpolation are not decoded. Applying one to
the entire crystal would be a custom tint, so the inspector does not do that.

The Phase 6A `F_GACHA_EFFECT_PATTERN_MST` / block table and repository
`effect_pattern_for` code relate awarded rarity/banner to an effect-pattern ID and
ordered block basenames. They are presentation metadata; Python remains the award
and currency authority. The previously documented missing block references and
nonstandard preservation rows still prevent treating that table as pristine retail
Global sequencing. No pattern/rate/backend field was changed here.

## Verified file structure: M3R / BR3M

The supported observed layout has little-endian fields and magic `BR3M`:

| Offset | Supported interpretation / validation |
| --- | --- |
| `0x04` | Raw revisions 34 and 35 observed; unsupported revisions rejected |
| `0x08` | One-mesh layout supported; other values rejected |
| `0x10` | Name region start |
| `0x14` | Material-record start |
| `0x18` | 16-bit index buffer start |
| `0x1c` | Vertex buffer start |
| `0x20` | Following uninterpreted tail start |
| `0x24`, `0x28` | End offsets equal to decoded file size in supported samples |
| material + `0x20` | Vertex stride, verified 36 bytes |
| material + `0x24` | Vertex count |
| material + `0x28` | Base field 0 in supported files |
| material + `0x2c` | Index count, multiple of three |

The supported material record is 88 bytes. Vertex interpretation:

```text
+0x00 float32[3] position
+0x0c uint32     packed attribute (retained raw; normalized RGBA is diagnostic)
+0x10 float32[3] normal
+0x1c float32[2] UV
stride 36 bytes
```

For model 001 (decoded size 37,944): names at 64, material at 96, indices at 184,
vertices at 2104, following tail at 36664. 960 uint16 indices are in range 0…959;
960×36 vertex bytes end exactly at the tail. Normals are finite and near unit length;
positions/UVs are finite. Y bounds are approximately −11.513 to +13.633. The 1,280
following bytes remain uninterpreted. The parser does not silently call them an
animation timeline or ignore them as a validated part of full BISHAMON playback.

Model 002 has matching vertex/index counts but different UV/material data. Other
observed model files (glow/cloud/particle) also validate the supported layout. This
is limited format support, not a universal M3R converter or full skeletal player.

## Isolated iOS prototype

Open **Developer → Crystal recovery → Inspect original crystal mesh**.

- SceneKit is used because the recovered content is actual 3D indexed geometry.
  SpriteKit alone cannot directly reproduce its model/material pipeline.
- Show, Restart view and Stop control inspection only. Dragging changes the camera
  by user input. There is no automatic turntable or fabricated original motion.
- “Play original animation” is visibly disabled with an explanation. This is an
  intentional recovery limitation, not a working animation advertised as complete.
- Idle inspection has no continuous render loop. Benchmark mode temporarily requests
  a 30 fps viewport cap; that cap is not recovered game timing or a measured guarantee.
- Scene lifecycle handlers suspend rendering and only resume a previously shown mesh.
  Leaving the preview stops it. Missing/checksum-failed data produces a safe message.
- Direct launch arguments `--crystal-preview` / `--crystal-diagnostics` route to this
  view before `ContentView` is constructed, avoiding Python/game initialization.
  The preview source has no backend, summon, campaign-file or URLSession entry point.

The normal Developer tab's parent application may already have loaded the campaign
for ordinary play; the inspector itself does not access it or send any transaction.
The direct diagnostic route is used for isolation tests. Reports/screenshots go only
under Application Support `FFBERevival/validation`, not the campaign directory.

## Retrieval, checksums and reproducibility

Only **304,733 response-body bytes** were newly fetched, through **21 exact HTTP
206 requests**. Five shared-effect CPK TOCs were inspected. Eleven selected members
were retrieved; no whole ZIP or large CPK was downloaded. Sources were:

- data-002 `Ver13_effectResource1_common.cpk`
- data-002 `Ver25_effectResource3_common.cpk` (TOC only)
- data-002 `Ver27_effectResource2_common.cpk` (TOC only)
- data-002 `Ver4_effectResource1_common_tutorial.cpk`
- data-002 `Ver70_effectResource_sg_common.cpk` (TOC only)

All live responses were exact bounded ranges using the existing throttled client.
Stored/decoded SHA-256 pins are in `crystal-dependencies.lock.json` and
`crystal-preview.lock.json`. CPK/ZIP source identity and offsets are retained.
Partial reads do not establish a whole remote archive checksum or retail Global
CDN authenticity. Provenance remains **Global-targeted preservation**, distinct from
original Global IPA and Memorial evidence.

```sh
cd ~/Documents/Projects/exvius-offline
# Existing cache: verifies without network. Fresh selected dependency cache:
# fetches only pinned small ranges, stops if exact HTTP ranges are unavailable.
python3 -B source/ios/content_tools/recover_crystal_dependencies.py

# Cache-only conversion; also requires the retained Phase 6A BMB/model inputs.
# Pillow is build-time only, in the tested system Python environment.
python3 -B source/ios/content_tools/import_crystal_preview.py
python3 source/ios/native/generate_project.py
```

The converter validates selected BMB structures/models but packages only mesh JSON,
one unchanged texture PNG, a findings catalog and checksum receipt. It emits immutable
versions under `.local/crystal-preview/versions/<lock-digest>/CrystalPreview`.
It refuses different bytes at an existing output version. Original sources remain
unchanged. No BMB, shader pack, client executable or CPK is put inside the app.
Xcode verifies/copies the optional bundle using standard-library Python; if absent
or corrupt, normal gameplay still builds and the diagnostic reports unavailable.

```sh
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6C1-Simulator \
  CODE_SIGNING_ALLOWED=NO build

xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6C1-Device build
```

Use the existing signing team and bundle ID. Run as an update; never uninstall.
The normal Phase 4/5C/6B runtime/content caches remain prerequisites.

Back up `.local/phase6a`, `.local/phase6c1`, `.local/crystal-preview` plus matching
source/locks. Keep original IPAs separately. These backups do not contain the normal
phone campaign and are not substitutes for a save backup. Game binaries/derivatives,
archives, build products and personal saves stay ignored and out of Git.

## Tests and performance scope

```sh
python3 source/ios/tests/test_crystal_preview.py
source/ios/.venv/bin/python -B source/ios/tests/test_summon_service.py
source/ios/.venv/bin/python -B source/ios/tests/test_offline_entry.py
source/ios/.venv/bin/python -B source/ios/tests/test_unit_content.py
```

Eight recovery tests cover actual geometry/texture identity, IBMB bounds, truncated
headers, unsupported layouts, invalid indices/non-finite geometry, checksums, missing
inputs, offline reproducibility, cache-only and fresh mocked range recovery, refusal
to overwrite corrupt cache, and source-level preview/backend separation.

`--crystal-diagnostics` exercises repeated inspection start/stop/restart, lifecycle
suspend/resume handlers, missing/corrupt bundle rejection, rendered snapshots and
performance measurements. It writes `crystal-report.json` and
`crystal-mesh-frame.png` under `FFBERevival/validation`. The original animation is
always reported as unrecovered. Snapshot latency is a static offscreen-render metric;
viewport callbacks measure only the observed static viewport. Neither establishes
original animation frame rate, timing or visual fidelity. A zero callback count is
not reported as a successful fps result. Resident memory is a whole-process sample,
not isolated GPU memory or a peak-memory profile.

Physical manual checks: open the Developer preview, drag, stop/restart repeatedly,
background and resume through the Home screen, force-close/relaunch, and repeat with
Airplane Mode and Wi-Fi off. Confirm normal Lapis, collection and saved results remain
unchanged. No normal-campaign summon is needed. Automated lifecycle-handler tests do
not claim the actual phone background/radio-off/reboot sequence was exercised.

## Remaining blockers and Phase 6C-2 recommendation

The geometry proves that a genuine recovered crystal can be rendered. It does not
establish full animation playback. Continue with a **BISHAMON compatibility probe**,
not production integration:

1. Map one BMB Model node to the model/texture names, constant color and vertex
   attributes; verify against an original/reference render before adding blue tint.
2. Decode one node's transforms and curves, including time units, interpolation,
   lifetime and coordinate space. Reproduce a verified still at a known time first.
3. Resolve texture overrides, blend/depth/cull modes, shader parameters, particles,
   random seeds and draw order. A generic SceneKit material is not the original shader.
4. Verify camera/projection and the n1/c1→c2→c3/c4 transition/input sequence using
   reliable Global evidence. Do not infer timings from filenames or a raw count.
5. Only then implement a minimal original segment and measure real playback/frame
   consistency on device. Metal/custom geometry/material playback may be required
   for faithful BISHAMON effects; SceneKit currently serves inspection only.
6. Keep the Phase 6B committed-response/result fallback boundary intact. Any eventual
   animation consumes already-awarded results; it must never invoke another summon.

No additional giant dataset download is presently justified: the principal immediate
blocker is renderer/schema understanding, not lack of a mother-crystal model. This
phase does not declare the original animation impossible; it identifies what is and
is not recovered so the next work can proceed without a fabricated substitute.


## Completed validation — 2026-11-06

- Xcode 26.2 Simulator and signed arm64 physical-device builds succeeded.
- 29 Python tests passed: recovery/import 8, summon service 7, offline entry 6,
  unit-content/save compatibility 8. The 423-unit artwork library is unchanged.
- Simulator and connected iPhone 16 Pro both rendered the recovered mesh and passed
  inspection start/stop/restart, suspend/resume handler checks and missing/corrupt
  content rejection. Missing-assets launch also displayed a safe fallback.
- Physical iPhone: 30.04 static viewport callbacks/sec at the 30 fps diagnostic cap;
  median snapshot 6.79 ms over 8 samples; whole-process resident sample
  117,145,600 bytes (111.7 MiB). Geometry-source/index data was
  49,920 bytes, plus a 128×128 RGBA texture (65,536 bytes before framework overhead).
- Simulator: 29.50 viewport callbacks/sec; median snapshot
  20.31 ms. These are inspection measurements, not original animation fps.
- On the phone, original/restarted snapshot PNG bytes matched. On Simulator they
  differed at 3,825 of 1,198,800 pixels (0.319%, maximum channel difference 158).
  That rendering repeatability difference remains unresolved. No claim is made of
  pixel-identical rendering across GPU/platforms or original-animation fidelity.
- Normal iPhone campaign bytes before the first update and after all diagnostics
  and ordinary startup were identical. No campaign restore/reset/uninstall or
  normal-campaign summon occurred. The phone and Simulator were returned to normal play.
- Packaged preview: 189,566 bytes. Signed Debug app: 42,157,413 bytes, an increase
  of 491,686 bytes over Phase 6B. Existing UnitContent (1,089,195 bytes) and SummonUI
  (1,293,965 bytes) stayed unchanged. No binary game assets are staged or committed.

The recovered animation is still **unavailable**. Show/Restart/Stop verify the static
inspector only; Play remains disabled. Actual Home-screen background/resume,
radio-off launch, reboot and user gestures remain the manual checks above.
The production summon flow and its backend were not replaced or modified.

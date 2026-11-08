# Phase 6C-3 — original-asset crystal reconstruction

The Developer preview now has Blue, Gold and Rainbow crystals, static layer
inspection, and reconstructed arrival, idle, opening and reveal-ready stages.
This is **not original BISHAMON animation recovery**. Original meshes and PNGs
are retained; materials, mappings, lighting, particles, timing and surface breakup
are authored reconstruction. Production summons still use the existing Phase 6B UI
and go directly to actual results. No transaction code was changed.

## Preservation and scope

Work started on `ios-port` with the Phase 6C-1/2 parsers, locks, documentation,
static inspector, Xcode/app/packaging edits and two `.DS_Store` files uncommitted.
Those changes were retained. The reconstruction is additive: a new component,
new immutable content bundle, and a link from the existing geometry inspector.
Its original gray-mesh diagnostic remains available. There was no reset, backup,
commit, upstream change, Android gameplay edit or iPhone app uninstall/update.

## Original resources and provenance

Six selected original preservation members were retrieved from data-002:

| Container | Member | Stored / decoded bytes |
| --- | --- | ---: |
| Ver4_effectResource1_common_tutorial | model_mothercrystal_003.m3r | 9,184 / 17,896 |
| same | model_mothercrystal_004.m3r | 20,712 / 37,880 |
| same | model_mothercrystal_005.m3r | 24,784 / 37,944 |
| same | deff_mothercrystal_004.png | 628 / 628 |
| same | prismatic_01.png | 7,744 / 7,744 |
| Ver13_effectResource1_common | deff_mothercrystal_002.png | 2,841 / 2,841 |

Container prefix is `native/common_lang/sd/effectResource/`, suffix `.cpk`.
Total selected stored payload is **65,893 bytes**. Retrieval used the existing
throttled exact-HTTP-206 range client, ZIP local-header/CPK TOC parser and CRILAYLA
decoder. No whole ZIP, CPK or preservation dataset was downloaded. Full-archive
hash identity cannot be established by partial reads. Provenance remains
**Global-targeted preservation**, not proof of retail Global CDN byte identity.
No third-party Godot/Effekseer runtime, converted model or texture is bundled.

The first validations exposed real format distinctions: models 003/004 have eight
`0xBA` vertex-alignment bytes; the parser now accepts only zero or eight such bytes.
Opaque effect textures use PNG CRC, chunk, scanline and dimension validation without
the unit-art-specific transparency requirement. Early rejected decoding attempts
were retried after these distinctions were understood. The retained last-pass
network journal is not a cumulative transfer total; it must not be confused with
the 65,893-byte unique payload total.

`crystal-reconstruction.lock.json` records source archive/container/member paths,
TOC/index hashes, offsets, lengths and stored/decoded SHA-256 pins. Retrieval checks
member identity against the pinned index and refuses changed/corrupt existing cache.
Original source bytes stay unchanged under ignored `.local/phase6c3/sources`.
Previously pinned models 001/002, texture 001 and three glow/burst textures are
reused from Phase 6C-1. The importer is cache-only and never opens campaign files.

All five original models now compare with the third-party conversion evidence:

| Original model | Vertices | Triangles | Internal texture basename |
| --- | ---: | ---: | --- |
| 001 | 960 | 320 | deff_mothercrystal_001 |
| 002 | 960 | 320 | deffuse_cloud_001 |
| 003 | 450 | 150 | space_003 |
| 004 | 958 | 320 | deff_mothercrystal_001 |
| 005 | 960 | 320 | deff_mothercrystal_002 |

Positions, normals and packed color words match the corresponding converted models
at every vertex. Converted UVs match after V inversion within 1e-7. That comparison
is evidence only: the app uses the original M3R coordinates, UVs and indices, with
**no Effekseer UV or triangle-winding conversion**. Model 003 is a partial shell;
its original purpose remains unknown. It is never identified as original shards.

## Layers and reconstructed appearance

The [2016 developer interview](https://game.watch.impress.co.jp/docs/interview/740405.html)
shows base, gloss and reflection/highlight layers combined with glow and particles.
It guides visual construction, without establishing numbered-file roles or Global
9.1.0 material/timeline parameters. Phase 6C-2 and third-party investigation reports
remain the structural/provenance references.

Default reconstruction choices:

- Base: original model 001 with original texture 001, reconstructed Blinn lighting,
  blue/gold multiplication, weak RGB emission and 0.95 pose opacity.
- Rainbow: the same mesh/UVs with original `prismatic_01.png`, constant lighting,
  reduced overlay opacity and multicolored particle tints. This texture assignment
  is reconstructed, not a recovered original node binding.
- Gloss: model 002 with scrolling original `glow_013` caustics, additive blending,
  slight layer separation and 0.24 opacity (0.10 for rainbow). Its internal cloud
  texture dependency is not supplied here; this is an explicit material override.
- Facets: another pass of the base geometry, using original texture 004, additive
  blending and 0.19 opacity (0.07 rainbow). This is an authored highlight mapping.
- Optional partial 003: disabled initially, with a labelled reconstructed caustic
  override because its `space_003` binding is unresolved. No original role claimed.
- Comparison switch: replaces 001/002 with original 004/005. Model 005 then uses
  its matching original texture 002. The original numbers do not determine roles.
- Glow/beam/flash: billboards using unchanged original `glow_003` and `lightburst_011`
  images; dimensions, tint, blend/depth state, bloom and opacity are reconstructed.
- Particles: 28 fixed, reusable billboards using those original images. Distribution,
  drift, sparkle and burst motion are deterministic authored functions, not BMB data.

Packed per-vertex words are retained and interpreted as normalized RGBA, continuing
an explicitly unverified shader interpretation. Camera, lights, transparency,
culling/depth choices and HDR bloom are reconstruction settings. Static controls
expose each contribution; both original model pairs and the partial shell are
inspectable independently of playback.

## Playback and future integration boundary

`CrystalPlayback.swift` is a Foundation-only clock and deterministic pose function.
Authored source time is seconds:

| Stage | Time | Reconstructed behavior |
| --- | --- | --- |
| Arrival | 0–0.90 | Smooth scale-in and settling movement |
| Idle | 0.90–2.55 | Small floating/turning motion, texture drift, particles |
| Opening | 2.55–3.75 | Flash, surface-cluster separation and fade |
| Reveal ready | 3.75–4.15 | Clear viewport, complete transition |

The opening partitions all original base triangles into 12 spatial groups and
moves/rotates those groups. Vertices/UVs remain original; grouping and motion are
reconstructed. The groups are open surfaces, not physically closed original shard
models. No fabricated original fracture resource is claimed.

The renderer uses a weak CADisplayLink target, cached scene nodes and materials,
no per-frame model/resource loading, and UI timeline updates capped near 10 Hz.
Render target is 60 fps; long scheduling gaps are capped at 100 ms of source-time
advance to avoid sudden jumps. Under heavy stalls, wall-clock duration can increase.
Speed ranges from 0.25× to 2×. Pause/static inspection/Stop invalidate display links.
Background/inactive events pause without auto-resuming; Play resumes explicitly.
Repeated Play/Restart does not accumulate scenes or particle emitters.

`CrystalReconstructionController` takes an appearance and exposes a completion
callback with `finished`, `cancelled` or `unavailable`. It does not accept reward
pools, costs, unit IDs or backend objects. Completion fires once per playback;
Stop/cancellation cannot cause a transaction. Missing/corrupt content yields a
safe unavailable view. The existing production result presentation is untouched.

For Phase 6C-4, wrap this component around **one already committed backend result**.
Choose appearance from the awarded rarity, bind the actual unit to reveal, and
advance through the actual multi-result array. Never call summon during playback,
restart, skip or reveal. Cancel/unavailable should route to the existing real-results
fallback. Preserve pending committed results across lifecycle interruption before
adding the component to production. That integration is not implemented here.

## Import, rebuild and run

From the repository root:

```sh
cd ~/Documents/Projects/exvius-offline
python3 -B source/ios/content_tools/recover_crystal_reconstruction.py
python3 -B source/ios/content_tools/import_crystal_reconstruction.py
python3 source/ios/native/generate_project.py
```

Existing Phase 6C-1 source cache and the normal embedded-Python/unit/UI prerequisites
remain required. Recovery reuses checksum-valid cache without network; fresh cache
retrieves only bounded pinned ranges and stops on unsupported ranges or rate limits.
Import writes an immutable bundle under
`.local/crystal-reconstruction/versions/<lock-hash>/CrystalReconstruction`.
All five mesh JSONs, seven unchanged PNGs, a provenance catalog and receipt are local.
Build packaging verifies hashes before copying this optional Developer bundle.
Missing reconstruction content does not disable normal gameplay.

```sh
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6C3-Simulator \
  CODE_SIGNING_ALLOWED=NO build

xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6C3-Device build
```

Normal navigation: Developer → Inspect original crystal mesh → Open animated
crystal reconstruction. After force-closing and reopening, the app returns to its
normal screen; temporary diagnostic launch arguments do not persist. Use this
Developer path to return to the preview. Launch arguments `--crystal-reconstruction` and
`--crystal-reconstruction-diagnostics` route directly to the isolated preview,
bypassing campaign/backend initialization. `--crystal-assets-missing` tests the
safe unavailable state. The old `--crystal-preview`/`--crystal-diagnostics` routes
retain the original static inspector.

## Tests and manual iPhone checklist

Run each suite in its own process, as established in earlier phases. System Python
runs `test_crystal_reconstruction.py`, `test_crystal_preview.py`,
`test_crystal_analysis.py`, `test_summon_ui_assets.py` and `test_artwork_batches.py`.
Use `.venv/bin/python` for service, offline-entry, unit-content, API and native-client
suites. The new nine-test suite includes a Swift clock executable and validates
fresh mocked six-range retrieval, cache checksums/identity, rejection of conflicts,
opaque texture integrity, observed BA padding, original coordinates/UVs, immutable
reproducible offline imports and absence of transaction/network entry points.

The in-app reconstruction diagnostic renders three appearances and arrival/opening
frames, tests layer/model toggles, pause, stop/restart, inactive-state handling,
24 repeated cycles, a single completion, missing/corrupt content and weak controller
release. It writes reports/images only under `FFBERevival/validation/reconstruction`.
Node-count stability and controller release are useful leak checks, not a substitute
for long Instruments runs on the iPhone. Actual Home-screen backgrounding, airplane
mode, reboot and phone touch controls still need manual execution.

When your iPhone returns:

1. Open the existing Xcode project and keep the existing team and bundle identifier
   `com.example.ffberevival.dev`. Run as an update; **never uninstall**.
2. Optionally set `--crystal-reconstruction-diagnostics` to exercise the isolated
   preview without loading the real campaign. Inspect all three appearances.
3. Use Play/Pause/Restart/Stop, speed and scrub controls. Toggle every layer; compare
   004/005 and optional 003. Confirm static inspection freezes motion.
4. During playback, go Home and return. It must be paused; press Play to resume.
   Repeat after force-close/relaunch and with Airplane Mode and Wi-Fi off.
5. Repeat playback many times; check Instruments Allocations/Leaks and frame pacing.
   Check the reconstructed open surfaces, transparency and bloom on the phone GPU.
6. Remove diagnostic arguments for ordinary play and verify your existing balance,
   inventory and campaign after relaunch/reboot. Do not spend currency merely to
   validate preservation. No existing iPhone campaign was reset or copied here.

Keep ignored content caches with the existing preservation sources and matching
locks when you make your own backup after Phase 6. No backup was created now, and
no original assets, downloaded archives or generated app bundles should enter Git.

## Completed validation — 2026-11-06

- **65 Python tests passed**, including nine new reconstruction tests. Swift clock,
  exact-unit display and HTTP client smoke checks also passed within their respective
  suites. Each suite used its documented interpreter and its own process.
- Xcode 26.2 Debug Simulator and signed **arm64 iOS** builds succeeded. The device
  binary's architecture was checked, and `codesign --verify --deep --strict` passed.
  The physical iPhone was not installed, launched or inspected in this phase, as
  requested. Device execution/performance remain pending when it returns.
- Final Simulator reconstruction diagnostics passed all three appearance renders,
  layer/model toggles, pause freeze, stop/restart, inactive handler, single completion,
  missing/corrupt rejection, 24 repeat cycles and controller release. Scene node
  count stayed at 52. Captured frames include arrival, opening and all three rarities.
- Final full-sequence sample: 225 callbacks over 4.37 seconds, **51.45 callbacks/sec**;
  median callback interval **16.67 ms**, 95th percentile **34.86 ms**. These are host
  Simulator callback measurements, not guaranteed presented-frame FPS or iPhone
  performance. An earlier optimized run measured 55.40/sec; occasional frame drops
  and host contention remain visible. Target is 60 fps, not a claim of a locked 60.
- Resident process sample before/after 24 snapshot-heavy repeat cycles was
  198,918,144 / 182,890,496 bytes in the final run. An earlier run grew about 6.9 MiB.
  Scene/controller ownership checks passed, but memory samples include framework/GPU
  caches and do not prove absence of all leaks. Physical Instruments profiling and
  longer continuous runs are still recommended.
- The retained original gray-mesh inspector also passed its original Simulator runtime checks.
- The existing summon UI's separate diagnostic campaign passed single, multi,
  duplicate-submission protection, insufficient-currency handling, saved-result
  retention, missing UI fallback and four rendered widths. It decoded all 11 UI
  assets. Normal campaign summons were not used.
- The Simulator's normal campaign SHA-256 before/after the app updates and tests
  matched. Only the hash was retained; no campaign copy/restore/reset occurred.
  Actual iPhone save/reboot integrity was not tested in this phase.
- UnitContent (1,089,195 bytes), SummonUI (1,293,965) and the old CrystalPreview
  (189,566) are byte-identical to Phase 6C-2. New CrystalReconstruction is 776,237
  bytes across 14 files. Signed Debug app is 43,429,080 bytes, **1,271,667 bytes larger**
  than Phase 6C-2. No game binary or generated content is staged or committed.
- Runtime preview resources are bundle-local, and component code has no network or
  summon entry points. Actual radio-off/Home-screen/reboot tests remain manual.
  Native Simulator UI automation timed out; no successful actual Home-button test
  is claimed. Programmatic lifecycle-handler checks passed.

Remaining limitations: reconstructed rather than recovered shaders/timing; unknown
original model-layer roles and several texture bindings; open-surface fracture
clusters; no real summon integration; no physical-device execution yet. Phase 6C-4
should begin with on-device appearance/performance/lifecycle review, then connect
one committed result to the reusable completion/fallback boundary above.

Captured appearance frames use SceneKit snapshots. The actual HDR viewport can look brighter, as the full Developer screenshot shows. Snapshot/viewport tone mapping and the physical display need device review; no pixel-identical capture/display claim is made.


## Physical iPhone validation follow-up — 2026-11-07

The app was updated in place on the iPhone 16 Pro without uninstalling it. The
campaign hash before/after both updates and isolated diagnostics matched. Temporary
save reads were deleted; no save backup was retained. Actual production summons
were not used for testing.

The reconstruction passed three appearance renders, layer/model toggles, pause,
stop/restart, missing/corrupt rejection, one completion and controller release.
Physical playback measured 59.86 callbacks/sec, with median/p95 intervals of
16.67/16.67 ms. These are display-link samples, not a direct GPU frame counter.
The user confirmed actual Home-screen pause/resume works correctly.

The memory test itself needed refinement: an unpooled synchronous snapshot batch
retained temporary capture buffers through its immediate measurement. Only the
diagnostic was changed to pool captures, warm up/cool down and measure live
restarts separately. In the refined run, resident samples were 78,151,680 bytes
after warm-up, 72,974,336 after 24 snapshot cycles and 68,059,136 after 24 short live
restart cycles. Scene nodes remained 52; the controller released. This sample shows
no sustained growth, but longer Instruments/thermal tests remain useful.

Nine reconstruction tests were rerun successfully; the new signed arm64 build and
signature check passed. On-device summon UI diagnostics passed single/multi,
duplicate protection, insufficient currency and saved-result retention using a
separate diagnostic campaign. Renderer/material/timeline/backend code was unchanged
in this follow-up. The detailed dated report and phone-captured frames are delivered
in the chat outputs. Reboot and longer profiling remain manual checks.

The user additionally confirmed cold relaunch and successful Developer-preview playback with Airplane Mode on and Wi-Fi off. This completes the physical offline-playback check; reboot and long thermal/Instruments tests remain unperformed.

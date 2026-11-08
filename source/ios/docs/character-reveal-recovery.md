# Phase 6D-1 — character reveal recovery

Research performed on `ios-port`, 2026-11-07. Existing uncommitted Phase 6C work is
preserved. Production result, transaction, crystal renderer and tap-state files
are unchanged from the beginning of this phase. No Phase 6D-2 integration occurs.

## Finding

We possess original preserved **acquisition/reveal artwork**, including a cyan
oval glow, cosmos background, obtained text, stars and rarity flares. We have
**not confirmed a distinctive solid pedestal or engraved magical-circle platform**
for the initial Global summon reveal. The cyan `getglow` is the strongest usable
under-character candidate, but its original on-screen placement is not decoded.
A static Developer gallery is provided for visual review, not as a finished
historically exact reveal.

The source is Global-targeted preservation, not proof of byte-for-byte retail
Global CDN origin. The gallery uses no Memorial/JP or third-party artwork.

## Search scope and provenance

- Original Global 9.1.0 recovery ZIP:
  `/Users/marcusmoore/Documents/Projects/FFBE Assets/6AF1D8E1-7409-46BC-A496-26D70EE90D0F.zip`.
  Prior source identity SHA-256: `92227543f76b496dd8dc4715ffcbe0e41b494197c5b2e597349ad7a248668c46`.
  Current archive central directory inspected read-only. Cached original-client
  CPK listings and Global layouts were reused, not the encrypted executable.
- English-patched JP Memorial 11.1.0 IPA:
  `/Users/marcusmoore/Documents/Projects/FFBE Assets/FFBE-Memorial-EN-iOS-Patch-5-Slim-r3.ipa`.
  Prior identity SHA-256: `247b2d61573f0967f4ed13a9df9089a7030ec5e73276a83c6fcf4776499b54b7`.
  Atlas candidates were extracted separately and labeled. Similarity does not
  merge provenance or unit IDs.
- Global-targeted preservation: repository `data/latest.json` and retained indexes
  for exvius-data-001 through 011. Reused Phase 5 unit CPK indexes, Phase 6A
  resource/dependency indexes and Phase 6C effect-resource indexes. This is a
  targeted indexed search, not an assertion that every member of every archive
  has been downloaded or visually examined.
- Third party: `/Users/marcusmoore/Documents/Projects/FFBE Assets/Other-Revival/ExviusReborn-Android.zip`;
  central directory plus retained 172,689-entry Godot PCK index and existing
  third-party investigation evidence. Nothing executed or copied into the app.
  Broad magic-circle name matches include character/battle effects and are not
  evidence of a summon pedestal. No Windows package exists in this location.
- Earlier research is also present outside the repository in the chat workspace
  `work/phase5-client-inspection` and `work/third-party-revival`. The former's
  18 original/client/tutorial CPK listings contain 4,375 entries and were searched.
- Repository caches inspected: `.local/phase6a`, `phase6c1`, `phase6c2`, `phase6c3`,
  `crystal-preview`, `crystal-reconstruction`, `summon-ui`, `unit-content`.
  `.local` is ignored. No saves or generated runtime/build trees were asset inputs.

Archive size/mtime remained unchanged during read-only directory inspection.
Prior whole-archive hashes above are inherited identity evidence, not newly
recomputed whole-archive hashes. Exact selected source/decoded/output hashes are
newly checked and recorded in the locks and research manifests.

## Candidate assessment

| Candidate | Source and evidence | Assessment |
| --- | --- | --- |
| `getglow`, 136×44 | `exvius-data-010.zip`, `native/en/sd/gacha/Ver2_gachaeffect1.cpk`, `gacha_result_animation.ssbp` / PNG. `ins_get` has two default-cell references to `getglow`, additive blend code 2. `gacha_get` and `gacha_rare3` reference `ins_get/anime`. | **Probable acquisition glow**, strongest floor-like candidate; original position, scale and timing unverified. |
| `starglow`, 216×80 | Same package; `ins_stlight` default cell. | **Possible** comparison; star-presentation glow, not a confirmed ground platform. |
| `stLight_3`, `_4`, `_5`, 256×256 | Same result atlas; blue, gold, rainbow radial flares. Rarity-named animation packs exist. | **Possible** reveal accents; no claim that these are platforms or that exact runtime rarity routing is decoded. |
| `cosmos`, 324×694; star and obtained cells | Same package, actual result animation cells. | Confirmed stored result artwork; original composition/keyframes not played here. |
| Newer result atlas, including NV+ oval/ring | `Ver162_resources_tutorial` plus required second page in `Ver202_resources`. | Separate version, shown in contact sheets only; do not use NV+ treatment for Maria 3★. |
| `gacha_plate_unit`, `gacha_base_step`, name panels | Preservation and Memorial TexturePacker frames, restored with trimming/rotation logic. | **Unrelated** to a ground pedestal: rectangular UI panels/labels. |
| `gacha_base_002_c1..5.bmb` | Name tables reference mothercrystal models and crystal textures. | Crystal effects; name “base” does not identify a character base. |
| `gacha_stage_common_c1..3.bmb` | Reference `model_cape_001/002`, `deff_cape_001`, glow and aura resources. | **Possible stage/background**; recovered texture depicts a rocky blue-crystal mound. Not confirmed as the remembered character pedestal. |
| `model_plate039_lightline.m3r` | 42 vertices, 60 triangles; nearly flat Z, Y −243.18 to 0; texture `prismatic_01`. | Tall light-effect mesh, not evidence of a horizontal unit pedestal. |
| `battle_unit_get*` BMB | Includes crystal/aura/ice/lightning dependencies. | Acquisition-family candidates; battle naming and table names alone do not establish initial gacha reveal usage. |

Global `layout_gachaEffect_640x1136.csv` contains only a `unit_image` anchor
(288,559,64,54; default Rain filename) and `unit_comment` (0,693,640,200).
It supplies no named pedestal texture. This absence in one layout is not proof
that the original effect system had no platform.

## Additional bounded recovery

Five members from `exvius-data-002.zip` /
`native/common_lang/sd/effectResource/Ver13_effectResource1_common.cpk` were read:
`model_cape_001.m3r`, `model_cape_002.m3r`, `model_aura_017.m3r`,
`deff_cape_001.png`, `glow_014.png`. Total: **244,135 bytes** in exact HTTP 206
ranges. Existing pinned index/TOC hashes and member bounds were checked. Stored
and CRILAYLA-decoded lengths/hashes are pinned. No full ZIP/CPK download occurred.

`model_aura_017` decodes as a horizontal 174-vertex, 264-triangle mesh. Both cape
models fail the existing strict decoder's buffer-layout checks. Those failures
are retained as explicit limitations; the decoder was not loosened to guess a
rendering. BMB animation/material bindings remain undecoded.

Four Maria animation members from `exvius-data-008.zip` /
`native/common_lang/sd/unit/Ver24_unit1_common.cpk` were retrieved: sprite sheet,
CGG composition CSV, idle CGS and standby CGS. Total **23,273 bytes**. Combined
new content transfer: **267,408 bytes**. All requests were bounded, throttled,
206-validated; no full-download fallback. No binaries executed.

## Character presentation and animation availability

Maria **202000203** is an exact-ID 3★ catalog row and has bundled static artwork.
The preview uses that exact ID, not a name-based substitute; its image remains
nearest-neighbor scaled. Existing other Maria forms remain separate IDs.

Recovered `unit_anime_202000203.png` is a sprite-part sheet; CGG supplies
composition records. `unit_idle_cgs_202000203.csv` contains four rows with leading
indices 0,1,2,3 and final values 12; standby contains indices 4..7 and final values
6. Those raw values are not labeled as milliseconds or fps. Rendering requires
validated part transforms, ordering, frame references and time units, not simply
cycling equal rectangles. No unit animation engine was implemented.

Result SpriteStudio v1 definitions preserve hierarchy, instances and blend modes.
This phase uses bounded **static cell crops only**, not original timeline playback.
Static character + additive glow + cosmos + name/awarded rarity can be composed
now. Exact platform identity, original timing, animated idle, original star
placement and crystal/reveal synchronization still require validation.

## Architecture and isolated preview

Current `GlobalSummonScreen` receives a committed receipt, presents
`SummonCrystalPresentation`, then `reveal` copies immutable `receipt.awards` into
`presentedAwards`. Completion/Skip/fallback converge on the existing
`GlobalSummonResults` adaptive grid. Single and 11-pull results share this grid.
Names come from `UnitCatalog`; awarded rarity is passed with `isAward: true`.
Codes 1–6 currently render a numeric label plus ★, not original star artwork;
other codes remain explicit. The plain result-list fallback uses `UnitRowView`.

The future dedicated reveal composition belongs **between** committed crystal
completion and that reliable grid; do not attach a pedestal to every shared
`UnitArtworkView` (which is also used by collection and lists).

Open **Developer → Inspect reveal artwork candidates** after rebuilding.
Or launch with `--reveal-research-preview`: this bypasses `ContentView` and normal
campaign initialization entirely. It displays fixed sample Maria, selectors for
five cells, background/unit/candidate toggles and explanatory labels. It does not
represent a newly awarded unit. Layer order: dark background → cosmos → additive
candidate → exact-ID sprite → native name/rarity label. Placement and scale are
explicitly reconstructed. Missing images produce a message/normal artwork
placeholder. Static SwiftUI images only: no animation timer, task, SceneKit nodes,
backend call or campaign reference. Images are scoped to the view; long memory
profiling was not performed and no blanket leak-free claim is made.

Only seven research PNGs are optionally bundled, totaling **542,446 bytes** plus
small JSON receipts. Stage models and Maria's animation research remain ignored
local files and are not bundled. The importer refuses altered sources/outputs;
optional missing research content does not disable normal gameplay.

## Reproduce and build

From `/Users/marcusmoore/Documents/Projects/exvius-offline`:

```sh
python3 source/ios/content_tools/recover_reveal_stage.py
python3 source/ios/content_tools/recover_reveal_unit.py
python3 source/ios/content_tools/import_reveal_research.py
python3 source/ios/content_tools/inspect_reveal_research.py
python3 -m unittest discover -s source/ios/tests -p test_reveal_research.py -v
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath /private/tmp/FFBERevival-Phase6D1-Simulator CODE_SIGNING_ALLOWED=NO build
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -derivedDataPath /private/tmp/FFBERevival-Phase6D1-Device build
```

The existing runtime/unit/UI/crystal caches remain prerequisites. Unit research
recovery intentionally requires its pinned retained Phase 5 CPK index; it stops
if absent/changed. Atlas import is cache-only. Contact sheets default to ignored
`.local/phase6d1/contact-sheets`; `--output PATH` selects a report directory.
Keep `.local/phase6d1`, the Phase 6A cache, and retained Phase 5 indexes together
when making a future content backup. No backup was created in this phase.

## Validation and Phase 6D-2 recommendation

Both Simulator and signed arm64 device builds succeeded. Existing 68 tests plus
7 new research tests passed, each suite in a separate process. New tests cover
reproducibility/offline import, source and derivative corruption, no overwrite,
invalid pointers/crops/duplicates, missing pages, cache-only bounded-recovery
verification and preview isolation. Simulator gallery was launched in isolation
and visually inspected. Existing embedded-backend/tap/crystal diagnostic also
passed in a separate temporary Simulator campaign. No normal campaign summon
was performed. No iPhone installation, launch, save access or device execution
was performed in this phase; a signed build is not physical execution evidence.

Normal production results, transaction, crystal and tap-state source hashes match
this phase's baseline. Python/Android gameplay is untouched. Nothing was staged,
committed or pushed. Local images/archives remain excluded from Git.

Next: review the gallery appearance first. If the cyan glow is acceptable, add a
separate committed-award reveal view after crystal completion. Feed it only the
immutable receipt, exact master ID and granted rarity. Maintain a frontend-only
cursor through multi-awards, a once-only completion gate, Skip and lifecycle
recovery, and retain the existing grid as fallback. Never call the backend from
reveal/Next/Skip. Do not bind rarity to unverified atlas variants. Decode original
SpriteStudio timing or explicitly approve reconstruction before animating. If the
remembered solid platform differs from these candidates, obtain a trusted Global
reference frame to narrow additional archive searches. **Do not implement this
production insertion until the appearance is reviewed and approved.**

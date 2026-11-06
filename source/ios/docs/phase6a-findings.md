# FFBE Revival — Phase 6A findings

Investigation completed 2026-11-06 on `ios-port`, following commit `f1f90c0`.
**No Phase 6B/6C interface or renderer was implemented.** The application, installed
iPhone app, Python gameplay, Android implementation and campaign files were not
changed or launched during this investigation. Phase 5C’s content cache and locks
were left intact. New game resources exist only in ignored local recovery storage.

## Assessment

Enough original layout and preservation artwork has been recovered to plan a
faithful static summon interface and a result/reveal prototype. We cannot yet claim
a faithful crystal-drop/break animation: those effects are not solely SpriteStudio.
They include a separate binary `.bmb` system, whose decoded payload begins `IBMB`,
and model/material-related resources. Replacing them with an invented sparkle
animation would not satisfy the historical-fidelity objective.

The recovered pattern/block tables provide useful ordering evidence, and the
SpriteStudio files expose real frame counts and 30 fps timing. These establish
building blocks, **not a completely verified client state machine**. Tap gates,
crystal upgrades, skips, sound synchronization and multi-result placement need
additional client/runtime evidence or a trusted recording before being called exact.

## Sources, provenance and verification

| Source | Identity | What it establishes |
| --- | --- | --- |
| Original Global recovery ZIP | `6AF1D8E1-7409-46BC-A496-26D70EE90D0F.zip`; SHA-256 `92227543f76b496dd8dc4715ffcbe0e41b494197c5b2e597349ad7a248668c46` | Contains nested client ZIP at `6AF1D8E1-7409-46BC-A496-26D70EE90D0F/1078553808`; bundle `com.square-enix.ffbeww`, version 9.1.0 / 9100 |
| English-patched Memorial IPA | `FFBE-Memorial-EN-iOS-Patch-5-Slim-r3.ipa` | Separate patched client, not original Global; exact source SHA-256 and bundle metadata are in the inventory |
| Global-targeted preservation | Repository `data/latest.json`, revision 9, version `2026.11.04.9` | Content packages used by the fork; may include repairs/recovery and cannot establish original retail Global CDN byte provenance |
| Custom recreation | None created in Phase 6A | Future substitutes must be explicitly labeled and reviewed |

The originals were opened read-only and their complete source hashes checked against
the earlier audit. ZIP CRC checks are performed by Python’s ZIP reader for local
members. CPK headers/TOCs and stored file bytes were inspected; CRILAYLA members
were decompressed with bounds checks and their exact decoded lengths checked.
SHA-256s for both stored and decoded bytes are recorded. PNGs were fully decoded
with Pillow, not merely accepted by extension. Plists were parsed and frame names
recorded. SpriteStudio v1 project/cell/animation headers and frame-pointer bounds
were parsed; **animation frame payloads have not been rendered**.

The machine inventory contains 490 focused resource records: 291 with actual bytes
retrieved/decoded and 199 CPK-TOC-only candidates. It separately includes outer ZIP
candidates, dependency CPK entries, audio cue tables, metadata rows, comparisons and
transfer receipts. Entries marked catalog/TOC-only are not verified usable assets.
An observed SHA-256 is a reproducibility pin, not a publisher-signed authenticity proof.
Whole remote ZIP/CPK hashes cannot be recomputed from partial byte ranges.

## Original Global client findings

All paths below are relative to `Payload/FF EXVIUS.app/` inside the nested client.

### Verified layouts: `cpk/layout.cpk`

There are 39 files under `layout/gacha/` (plus unrelated battle/mission summon
layouts outside that directory). The important exact resource families are:

| Purpose | Exact paths / variants | Format and evidence |
| --- | --- | --- |
| Banner list | `layout/gacha/layout_gachaTop_640x960.csv`, `_640x1024.csv`, `_640x1136.csv` | CSV coordinates, named regions, banner/scroll/tab references |
| Banner details | `layout/gacha/layout_gachaDetail_640x960.csv`, `_640x1024.csv`, `_640x1136.csv`; corresponding `layout_gachaDetail_work_*` | CSV; some members are CRILAYLA-compressed in the CPK, successfully decoded |
| Summon buttons | `layout/gacha/layout_gachaButtonL.csv`, `layout_gachaButtonR.csv`, `layout_gachaButtonTicket.csv` | Named button, price, badge and currency-icon anchors |
| Confirmation | `layout/gacha/layout_gachaConfirm.csv`, `layout_gachaPseudoPaidConfirm.csv` | Single/multi confirmation regions; text and price anchors |
| Reveal | `layout/gacha/layout_gachaEffect_640x960.csv`, `_640x1024.csv`, `_640x1136.csv` | Unit-image and comment anchors |
| Results | `layout/gacha/layout_gachaResultUnit_640x960.csv`, `_640x1024.csv`, `_640x1136.csv`; equivalent `layout_gachaResultItem_*` | Result areas and next buttons, not a complete generated multi-unit grid definition |
| Tickets/tabs/panels | `layout_gachaTab.csv`, `layout_gachaTicketListCommon.csv`, `layout_gachaTicketSelect.csv`, `layout_gachaPanelAcquire.csv`, `layout_gachaPanelDetail.csv`, `layout_gachaPanelLottery.csv` under `layout/gacha/` | Verified layout files; not all are needed for current single/multi banners |

Concrete evidence from the 640×1136 layouts:

- Detail banner anchor: `(0,250,640,392)`; left/right button offsets around
  `(2,653,304,136)` and `(332,653,304,136)`; ticket offset at `(2,795,304,136)`.
- Left button references `button/gacha_btn_n_default_l_1.png`, with distinct price,
  badge and icon anchors. Confirmation has separate single and multi cost regions.
- Reveal layout contains `unit_image` at `(288,559,64,54)` with the placeholder
  `unit_ills_100000102.png`, and `unit_comment` at `(0,693,640,200)`.
- Unit results contain `gacha_result_area1`, `gacha_result_area2`, two next-button
  anchors and `gacha_panel_result_offset`. They do not specify every result tile,
  draw order or spacing for arbitrary multi-summon sizes.

Coordinates are CSV values, not yet a validated SwiftUI transform. Their origin,
alignment and scaling semantics must be checked against the original engine.
The placeholder Rain ID is a layout default, not permission to substitute Rain for
an awarded unit.

### Global textures and audio actually present

`cpk/common.cpk` and
`cpk/common_lang/sd/resources/resources_common_pretutorial.cpk` contain
`font/gacha_step_num24.fnt` and `font/gacha_step_num24.png`. These are step-number
font resources, not proof that the full summon artwork is bundled in the base IPA.
The Global IPA does **not** contain a dedicated gacha CPK or SpriteStudio CPK in its
11 packaged CPKs. Its pre-tutorial language resources do not supply the missing
full gacha atlases/effect sets found in preservation content.

Original audio banks inspected:

- `ios/se/Builtin.acb` — 4 cues.
- `ios/se/System_tutorial.acb` — 40 cues.
- `ios/se/SE_tutorial.acb` — 16 cues.

`System_tutorial.acb` contains `se_event_cristal_break` (spelling as stored),
`se_ev_crystal_appeare`, `se_ev_crystal_disappeare` and result/menu sounds.
Those names do **not** prove they are the gacha break cues. No original-client
gacha sound schedule was recovered. Banks are CRI UTF/ACB with embedded audio data;
cue/waveform metadata was parsed, but playback/codec decoding was not tested.

The Global executable’s Mach-O encryption command has `cryptid=1` over a substantial
code region. Plain-string inspection yielded little gacha evidence. No encryption
bypass or executable modification was attempted. This limits direct verification
of the original Global state machine from this recovered binary.

## Memorial findings — kept separate

Under `Payload/FF EXVIUS.app/`:

- `cpk/layout.cpk`: 42 `layout/gacha/` layouts, including AdGacha variants.
- `cpk/resources.cpk`: `image/ui/gacha/gacha.plist` + `gacha.png`,
  `gacha2.plist` + `gacha2.png`, `gacha3.plist` + `gacha3.png`,
  `gacha_cosmos_bg.png`, `gacha_textbg.png`.
- `cpk/spritestudio.cpk`:
  `spritestudio/gacha_panel_animation/gacha_panel_effect_anim.ssbp` + PNG;
  `spritestudio/summonconduct_animation/summonconduct_animation.ssbp` + PNG;
  `spritestudio/summon_animation/summon_animation.ssbp` + PNG.

All 39 Global `layout/gacha/` paths have byte-identical decoded counterparts in
Memorial. Memorial adds three `layout_AdGachaList_*` files. This is verified layout
sharing only; it does not establish that the two clients use the same assets,
state machine or unit-ID namespace.

Atlas metadata: Memorial `gacha` is 977×1376 / 42 frames, `gacha2` 1013×1998 /
70 frames, `gacha3` 982×872 / 20 frames. These differ from preservation atlases
below. All six PNG/plist pairs were inspected from their actual bytes. Neither
shared filenames nor English patching make them interchangeable.

The SpriteStudio binaries identify `SSPB`, version 1, and an Ss5Converter build
string. `summon_animation` contains `summon_board_*`, `summon_lock` and
`rb_board_*` packs: it is evidence of board/unlock animation, **not evidence of the
gacha crystal-break movie**. `summonconduct_animation` has button/moogle/sparkle
parts and a 63-frame, 30 fps main pack; its exact use needs caller evidence.

Memorial’s unencrypted executable contains `GachaEffectScene`,
`GachaEffectMovieScene`, `GachaResultScene`, `GachaResultItemScene`, `ss::Player`
and Cocos-related type strings. This corroborates multiple scene/renderer systems,
but strings alone do not prove control flow or equivalence to Global.

`se/System.acb` has 119 cues, including `se_menu_get_unit1` through
`se_menu_get_unit4`, `se_menu_change_crystal_1`, and `se_event_cristal_break`.
`se/SE.acb` has 834 cues and `se/Builtin.acb` has 4. Exact cue indexes are in the
inventory. Sounds were not decoded or listened to, and no rarity-to-cue mapping
has been assumed.

## Global-targeted preservation findings

All remote data below used strict HTTP 206 ranges, exact Content-Range/length
validation, serial throttling and transfer budgets. There was no full-download
fallback and no rate-limit response. Total new archive response payload:
**8,446,157 bytes (8.06 MiB), 228 requests**. This includes TOCs and selected files;
no multi-gigabyte ZIP or large CPK was downloaded. Cached ZIP central directories
from Phase 5 were reused. Signed CDN tokens were not saved.

### `exvius-data-003.zip`

| CPK member | Actual content verified |
| --- | --- |
| `native/common_lang/sd/gacha/Ver12_gachaeffect1_common_tutorial.cpk` | Nine `.bmb` effects: `gacha_n1_c1/c2/c4`, `gacha_r1_c1/c2/c4`, `gacha_r3_c1/c2/c4` |
| `native/common_lang/sd/gacha/Ver31_gachaeffect1_common.cpk` | All 111 named members retrieved; crystal/background/backeffect/base/moogle/lapis effects, result effects, `.m3r` models, PNG textures and `gacha_animation.ssbp` |
| `native/common_lang/sd/gacha/Ver19_gacha1_common.cpk` | TOC inspected; actual `gacha_bg_blue.png`, `gacha_bg_yellow.png`, `gacha_bg_rainbow.png`, `gacha_bg_red.png`, `gacha_bg_white.png` retrieved and decoded |
| `native/common_lang/sd/gacha/Ver2_gacha6_common.cpk` | Outer ZIP candidate only; promotional content not needed for the first faithful generic summon flow |

The 111-member effect pack includes exact names such as:
`gacha_crystal_n1_c1.bmb`, `gacha_crystal_n1_c2.bmb`, `gacha_crystal_n1_c3.bmb`,
corresponding `r1/r2/r3` families, `gacha_background_*`, `gacha_backeffect_*`,
`gacha_base_002_c1.bmb` through `_c5.bmb`, `EX16_2openblue.bmb`,
`EX16_2opengold.bmb`, `EX16_2openraindow.bmb` (stored typo),
`EX16_1openedstill.bmb`, `EX16_3closedstill.bmb`,
`battle_unit_get_result2_3.bmb`, and other `battle_unit_get_result*` variants.
The inventory lists every exact member and both hashes.

Decoded `.bmb` headers begin `IBMB`; crystal payload strings include
`model_mothercrystal_001`, `model_mothercrystal_002`, `deff_mothercrystal_001`,
`deffuse_soccerball_001`, and `model_crystalparticle_001`. These suggest model and
material components, but the full format and whether particular named resources
are embedded or external are unresolved. Separate `model_cloud_002.m3r`,
`model_glow_009.m3r`, `model_plate039_lightline.m3r` files also exist. This is not
an ordinary plist sprite-strip animation.

### `exvius-data-010.zip`: English gacha assets

Verified selected members/contents:

- `native/en/sd/gacha/Ver58_gacha1.cpk`: TOC of 190 entries, 36 selected PNGs
  retrieved, including default left rare buttons, single/multi labels and other
  matching background/button resources. `gacha_btn_r_default_l_1.png` /
  `_2.png`, `gacha_btn_r_multi_1.png` / `_2.png`,
  `gacha_button_single_1.png`, `gacha_button_multi_1.png` are actual files.
- `native/en/sd/gacha/Ver18_gacha2.cpk`: TOC and two selected multi-button images.
- `native/en/sd/gacha/Ver15_gacha3.cpk`: eight TOC candidates; file bodies not fetched.
- `native/en/sd/gacha/Ver2_gachaeffect1.cpk`: all eight files retrieved:
  `gacha_panel_detail_anim.ssbp` + two PNGs, `gacha_panel_effect_anim.ssbp` + PNG,
  `gacha_result_animation.ssbp` + PNG, `touchscreen.png`.
- `native/en/sd/gacha/Ver9_gachaeffect1_tutorial.cpk`: actual `touchscreen.png`
  and `touchscreen_orange.png`.

Other `Ver0_*` and tiny `gacha4/gacha5` packages remain explicitly indexed candidates;
they were not all fetched or assumed equivalent to later versions.

### Core resources: data-006 and data-010

Six additional resource CPK TOCs were inspected without fetching whole packs:

- data-006: `native/common_lang/sd/resources/Ver101_resources_common_pretutorial.cpk`,
  `Ver172_resources_common_tutorial.cpk`, `Ver273_resources_common.cpk`.
- data-010: `native/en/sd/resources/Ver112_resources_pretutorial.cpk`,
  `Ver162_resources_tutorial.cpk`, `Ver202_resources.cpk`.

Selected actual resources from `Ver162_resources_tutorial.cpk` include:

| Exact path | Verified decoded contents |
| --- | --- |
| `image/ui/gacha/gacha.plist` + `gacha.png` | TexturePacker plist format 3; 53 frames, 1690×788 atlas |
| `image/ui/gacha/gacha2.plist` + `gacha2.png` | 74 frames, 1722×892 atlas |
| `image/ui/gacha/gacha3.plist` + `gacha3.png` | 16 frames, 918×572 atlas |
| `image/ui/gacha/gacha_cosmos_bg.png` | Actual decoded background PNG |
| `image/ui/gacha/gacha_textbg.png` | Actual decoded PNG |
| `spritestudio/gacha_result_animation/gacha_result_animation.ssbp` + PNG | Newer 42-pack v1 result animation; decoded SSBP is 915,164 bytes |

The newer animation also references `gacha_result_animation2.png`, actually
retrieved from `Ver202_resources.cpk` at
`spritestudio/gacha_result_animation/gacha_result_animation2.png`.
Thus both referenced texture pages are available. The earlier English gacha-effect
CPK has a 698,796-byte, 34-pack result animation. **These are distinct versions.**
Do not combine them by filename or assume NV+ tracks belong in the target Global era.

`Ver172_resources_common_tutorial.cpk` provides a newer
`layout/gacha/layout_gachaResultUnit_640x1136.csv` with extra confirm/reroll,
social-sharing and popup anchors. It differs from the original Global IPA layout.
For fidelity to Global 9.1.0, prefer the directly recovered Global layout until
specific later elements are independently justified. A reroll anchor does not
authorize implementing a reroll mechanic in our app.

### Metadata: `exvius-data-001.zip`

Actual ZIP members retrieved with decompression and CRC32 validation:

- `static/mst_decoded/F_ANIMATION_MST.ndjson`
- `static/mst_decoded/F_GACHA_EFFECT_BLOCK_MST.ndjson`
- `static/mst_decoded/F_GACHA_EFFECT_PATTERN_MST.ndjson`

There are 34 effect-block rows and 69 pattern rows. All 34 block asset basenames
have a retrieved matching `.bmb`. Example pattern block lists are
`1111,1112,1114` → `gacha_n1_c1`, `gacha_n1_c2`, `gacha_n1_c4`, and
`2221,2222,2224` → the `gacha_r1_*` tutorial family. This verifies an ordered
relationship in the data; it does not prove exact touch/skip handling or the units
of numeric timing fields such as `3hr5ziJf=330`.

`F_ANIMATION_MST` row 90001 explicitly references
`gacha_animation.ssbp#gacha_animation,gacha_moogle_rare/anime`; row 90002 references
`gacha_panel_detail_anim.ssbp#gacha_panel_detail_anim,gacha_panel_detail_anim/anime`.
The pattern table is not a complete, pristine historical schedule: rows 6229–6232
reference block IDs `8891`, `3391`, or `4491`, which are absent from the recovered
block table. Ten rows 990009–990018 for gacha `999001` use colon tokens such as
`3:100`, `4:75`, `7:30` instead of a plain block-ID list. Their semantics/origin
must be resolved before use; these are further reasons not to treat the preservation
tables as authoritative retail behavior. No changes were made to them or the backend.

The existing repository’s recovered client-schema comments independently describe
these resource keys. Those comments are secondary evidence from prior Android
reconstruction, not newly verified original Global iOS disassembly.

### Preservation audio

Only header/cue/waveform table ranges from data-010
`native/common_lang/sound/se/android/Ver15_System.acb` were fetched, not its whole
4,150,176-byte bank. Its 119-cue table contains `se_menu_get_unit1..4`,
`se_menu_change_crystal_1` and `se_event_cristal_break`.
`native/common_lang/sound/se/android/Ver36_SE.acb` (32,600,768 bytes) remains an
outer-index candidate. Filenames containing “Summon” in crossover BGM were not
mistaken for gacha music or downloaded.

The preservation bank is explicitly under `android`; byte/codec compatibility with
iOS playback is unverified. Candidate cue names do not establish synchronized gacha
usage. Recover exact CueID → sequence/synth → waveform mapping and decode/listen
to the selected waveforms before bundling them. Do not ship whole banks just to
obtain a few effects. Original Global tutorial audio remains a separate provenance.

## Animation technology and recoverable timing

Verified mechanisms:

1. CSV UI layouts with named anchors and referenced texture names.
2. TexturePacker format-3 PNG/plist atlases, with frame metadata.
3. SpriteStudio `.ssbp`, magic `SSPB`, version 1, paired texture pages.
4. `.bmb`/`IBMB` effect binaries and `.m3r` model-related binaries.
5. CRI UTF/ACB audio banks; decoding/playback still pending.

The samples do not establish that a video is the primary crystal sequence. A
Memorial `GachaEffectMovieScene` type string is only a hint; no matching summon
video stream was recovered/validated. Battle `CGG/CGS` CSV animation families also
exist in the repository/client inventory, but they are not evidence that gacha
crystal effects use those formats.

The v1 binary parser was checked against SpriteStudio’s historical official
[SS5PlayerData.h](https://github.com/SpriteStudio/ssbpLib/blob/2a80bf76d907/Players/ssbpLib/SS5PlayerData.h).
Its project/cell/pack/animation structures match the observed files. The modern
header has additional fields; a modern-format parser must not be applied blindly.
The official [SS5 player interface](https://github.com/SpriteStudio/ssbpLib/blob/master/Players/ssbpLib/SS5Player.h)
is a useful implementation reference, not proof of a ready-to-use current iOS port.

Verified selected clip timing from the older preservation result set:

| Clip packs | Frames / fps | Clip duration |
| --- | --- | --- |
| `gacha_moogle_normal`, `gacha_moogle_rare` | 60 / 30 | 2.0 s |
| `gacha_backlit1..7`, `gacha_backlitnv`, `gacha_backlitvc` | 60 / 30 | 2.0 s |
| `gacha_cosmos`, `gacha_get` | 120 / 30 | 4.0 s |
| `gacha_flash`, `gacha_new` | 30 / 30 | 1.0 s |
| `gacha_rare1..7`, `gacha_rarenv`, `gacha_star0..7`, `gacha_starnv` | 120 / 30 | 4.0 s |
| `ins_lightning` | 106 / 30 | 3.533 s |

These are individual clip lengths. They must **not** be added together as if every
clip plays sequentially; some are layers, loops or nested instances. User-data
callbacks and blend modes must be decoded before faithful playback.

## Evidence-supported flow and remaining unknowns

The layouts and master references support a structural flow of banner list →
detail/price buttons → confirmation → effect/reveal region → results/next controls.
The Python backend must finish its real transaction before presentation consumes
its awarded IDs/rarities. No client-side animation may roll a second result.

Still unverified:

- Exact Global crystal-drop/break/upgrade timing and which block variants play for
  each awarded rarity, banner and special case.
- Full `IBMB` frame, mesh, material, camera, blend and texture-binding semantics.
  Some internal resource names were not resolved in inspected TOCs; it is not yet
  known which are embedded versus external dependencies.
- Touch-to-break, long press/skip, animation cancellation, sound cue trigger times,
  loop boundaries and all SpriteStudio user-data events.
- Multi-summon crystal arrangement, reveal order, tile generation, and treatment
  of guaranteed slots. Layout anchors alone cannot prove the full grid.
- Exact target-era asset precedence when base IPA and downloaded pack versions
  differ. The recovered Global IPA is 9.1.0; the preservation corpus spans variants.
- Which visual effects represent rarity codes versus NV/NV+ special categories.
  Never infer backend awarded rarity from a color or asset suffix.
- Original summon music and verified gacha cue-to-waveform mapping.

## Rendering recommendation

Use SwiftUI for navigation, banner selection, confirmation, accessibility and result
collection controls. Use a contained SpriteKit scene for original 2D atlas cells,
transforms, layers and timed effects after validating a SpriteStudio v1 decoder.
A build-time conversion into a small versioned intermediate format can preserve
original frame timing while avoiding archive parsing in the installed app.

For SpriteStudio, preserve cell pivots, hierarchy, z-order, blend modes, opacity,
color/vertex changes, nested animations and event timing. Compare selected rendered
frames against a reference player before claiming fidelity. A minimal C++ reference
player adapter is another option, subject to license review and an actual arm64
build test; it is not pre-verified here.

Do not commit to SpriteKit alone for the crystal `.bmb` system. Determine whether
its model/effect data requires 3D projection or custom material/shader handling.
Metal or a suitable 3D host may be needed; that is a later technical decision.
SwiftUI keyframe animation alone is not a faithful substitute for unidentified
binary particle/model behavior.

## Proposed Phase 6B — reviewed static experience first

1. Review this inventory, choose Global 9.1.0 as the explicit visual target, and
   approve which preservation resources may supplement the base IPA.
2. Create a separate checksum-pinned summon-content lock/cache, leaving Phase 5C
   unit content intact. Resolve exact layout-referenced atlas frames and common
   window/button dependencies; do not assume all referenced textures are present.
3. Convert verified atlas frames/layout anchors into a documented build-time format;
   test rotation, trimming, pixel dimensions, frame uniqueness and missing resources.
4. Implement banner/detail/confirmation/result structure with the recovered assets.
   Keep current backend protocol, transaction, rollback and persistence untouched.
5. Results use actual awarded IDs and rarities, existing exact-ID unit sprites,
   and honest placeholders. Static display remains available if animation fails.
6. Test single/multi, insufficient currency, failure/retry UI, saved historical
   results, offline launch and same-name forms. Build Simulator and signed arm64;
   update-install without uninstalling or modifying the campaign.

Phase 6B should not claim full original animations. Any temporary transition is
explicitly marked a custom placeholder and approved before use.

## Proposed Phase 6C — animation and reveal

1. Decode a small SpriteStudio v1 clip end to end using the recovered PNG pages;
   verify transforms/blending and timing against the official reference player.
2. Establish the actual Global sequence from master joins plus a trusted recording
   or accessible client caller evidence. Record which parts are proven versus inferred.
3. Decode one `.bmb` crystal family and resolve embedded/external models/textures.
   Validate a still frame, then drop/idle/break segments. If blocked, stop that feature
   and report the precise unsupported command/resource, rather than inventing motion.
4. Map the backend’s actual effect-pattern/result data to a presentation timeline;
   support only verified variants initially. No animation-driven reward generation.
5. Recover selected audio waveforms, verify codecs and cue timing, and package small
   offline-ready derivatives with separate source/derivative checksums.
6. Add tap/skip, repeated results and multi-summon playback only after their sequence
   is evidenced. Interruption/relaunch must display saved actual results and never
   repeat a paid transaction. Keep the backend’s existing protections in force.
7. Profile on the iPhone 16 Pro, compare reference frames/timing and test Airplane
   Mode, background/resume and memory pressure before making the faithful mode default.

## Packaging, size and performance risks

Compressed file size is not texture memory. The preservation gacha atlases alone
are approximately 12.94 MiB of RGBA8 pixels before mipmaps/extra copies; result
animation pages and backgrounds add more. Load scene-specific textures, release
unused pages and measure peak memory. Preserve nearest-neighbor scaling for unit
pixel art; do not assume UI glows/backgrounds should use the same filtering.

Bake only the selected compatible asset version, not every duplicate CPK. Do not
pre-render every animation frame indiscriminately: that can multiply app size and
memory. Prefer atlas-driven frame data where fidelity permits. Bounded binary
parsers need size/count limits; runtime playback should read converted bundled data,
not remote archives. Audio decoding and model conversion remain explicit build-time
steps. No runtime networking is required or proposed.

No Phase 6 assets were added to the app, so its installed size is unchanged. The
8.06 MiB transfer is an investigation cost, not an app-size estimate. A real package
size estimate must follow a reviewed minimal dependency set and renderer prototype.

## Storage, reproduction and next decision

Ignored recovery cache:
`source/ios/.local/phase6a/` in the repository. It contains separate `global/`,
`memorial/`, `preservation/`, `decoded/` folders, range receipts and `audit-scripts/`.
Exact cache paths and source hashes are in `Phase-6A-Asset-Inventory.json`.
The scripts rely on the retained Phase 5 ZIP indexes in the chat workspace and the
existing content tools. They are investigation scripts, not a production importer.
Keep the cached indexes with the recovery backup if repeating the audit later.

Example backup, from the repository root:

```sh
ditto source/ios/.local/phase6a /Volumes/YOUR_BACKUP/FFBERevival/phase6a
```

Back up source IPAs separately without changing them. This is not a campaign-save
backup. No copyrighted binary, IPA, large archive or generated application should
be added to Git. The report/inventory contain paths, hashes and metadata only.

**Review gate:** agree on the visual target era, static Phase 6B scope, and the
`.bmb` fidelity investigation before beginning implementation. Neither Phase 6B nor
Phase 6C has begun.

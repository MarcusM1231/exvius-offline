# Phase 6C-2 — bounded BISHAMON structural recovery

No verified animated property was recovered. Original Play remains disabled. The
existing static SceneKit inspector and production summon flow are unchanged.
This is an analysis milestone, not a working original animation segment.
No backup, commit, campaign reset, uninstall or new asset download was performed.
Work remains on `ios-port`; all pre-existing uncommitted Phase 6C-1 work is retained.

## Reproducible evidence

`content_tools/crystal-analysis.lock.json` pins stored and decoded bytes separately
for the normal/gold primary effects and one ordinary tutorial effect, plus the
SHA-256 of the English-patched Memorial executable used for disassembly. Provenance
is Global-targeted preservation, not proof of retail Global CDN byte identity.
Memorial code is investigative evidence and has not been incorporated or executed.

Run from the repository root:

```sh
python3 -B source/ios/content_tools/analyze_crystal_bmb.py
python3 -B source/ios/tests/test_crystal_analysis.py
```

The cache-only analyzer writes `.local/phase6c2/bmb-analysis.json`. It validates
both hashes and lengths through the existing importer; it neither fetches data nor
rewrites source caches. It refuses to overwrite a differing report. No new runtime
resources are generated. Existing `.local/phase6a` inputs are required.
The lock contains exact archive/member/cache paths; missing or corrupt inputs fail.

## Primary normal crystal map

Source: data-003, `native/common_lang/sd/gacha/Ver31_gachaeffect1_common.cpk`,
`gacha_crystal_n1_c1.bmb`, decoded 29,536 bytes.
Decoded SHA-256: `7e4c776d1cea64fa2139645d46389afeb417f5380f97d4107fc6c65ef7eb8b27`.
Gold comparison: `gacha_crystal_r1_c1.bmb`, decoded SHA-256
`0898e7546528f0f70d1a55aa94f749af0134cf8b01dc68f9f4b751090cc0085f`.

Every record starts with little-endian u32 raw type at +0 and length at +4.
The exact scan starts at 0x60 and ends at the name region, 0x6380. These 16
records account for every byte of that region:

| Offsets | Raw type | Bytes each |
| --- | --- | --- |
| 0060, 0360, 0660, 0960 | 0 | 768 |
| 0c60, 1400, 1ba0, 2340 | 6 | 1,952 |
| 2ae0 | 0 | 768 |
| 2de0, 3580, 3d20, 44c0, 4c60 | 6 | 1,952 |
| 5400, 5bc0 | 3 | 1,984 |

The +8 counts support a complete preorder tree: 0060→0360→0660;
0660 has children 0960 and 2ae0; 0960 has four type-6 leaves;
2ae0 has five type-6 and two type-3 leaves. This is a consistent **hierarchy
candidate**, not a proven Global runtime parent/transform relationship. Type-3
records are model-node candidates. No model basename is assigned to either one.
The parser enforces observed type/size combinations, total region bounds, a
4,096-record/count cap and a complete connected preorder interpretation.
Unknown layouts are rejected, rather than read using nearby-version offsets.

The names occupy 0x6380–0x6430; later data extends to 0x7360. Names include
`model_mothercrystal_001`, `model_mothercrystal_002`, `model_glow_001` and texture
basenames already inventoried in Phase 6C-1. Name presence is not a node binding.
Raw header counts at 0x10 and 0x14 are **not** node counts or durations.

## Normal/gold comparison

There are exactly 21 differing aligned u32 words. Nine are in three type-6
records, at absolute offsets 0x31d0–0x31d8, 0x48b0–0x48b8 and
0x5050–0x5058. The other 12 occur after the name region. No word in either
primary type-3 candidate differs. Float candidates at 0x31d0 are approximately
(0, 0.6465, 1) versus (1, 0.7959, 0.2221). This supports a color-related
hypothesis, but does not establish a color module, interpolation or whole-model
tint. All 21 exact offsets/u32 values/finite float candidates are in the report.
No appearance change was made from these differences.

## Reader/layout compatibility blocker

The patched Memorial arm64 executable has a reader check at virtual address
0x100eb6068. It compares magic against IBMB and +4 against **0x01030101**.
The preferred primary normal/gold files instead have raw tag **0x51**.
Consequently this particular reader does not directly accept those bytes. This
does not prove that all Memorial readers reject them or that conversion is
impossible. No tag rewriting or assumed conversion was performed.

The same executable's traversal at 0x100eb6930 uses +8 as child count and +4 as
record stride. Its type switch maps raw type 3 to fixup helper 0x100eb71e4.
Many function entry instructions are patched trampolines. Nearby symbol labels
are not reliable function names for stripped helpers, and module work-buffer
sizes are not serialized parameter sizes.

Named Model module initialization wrappers give useful ABI clues:
translation constants at runtime parameter +0x2bc/+0x2c8; rotation +0x304/+0x310;
scale +0x34c/+0x358; corresponding curve structures +0x570/+0x590/+0x5b0.
These are relative to a pointer obtained from initialization context +0x10,
**not verified record-relative file offsets**. The missing context-to-file mapping
prevents assigning those labels to bytes, even on the compatible tutorial file.
They must not become an animation decoder without that mapping.

## Compatible tutorial evidence — kept separate

`Ver12_gachaeffect1_common_tutorial.cpk/gacha_n1_c1.bmb` is an ordinary tutorial
crystal effect, not EX16 chest opening and not a replacement for the primary
sequence. Its decoded hash is
`e9bf3adaade01cf472cb6a47601a2b689fe7164c81a3420ba967f929971ea3e8`.
It has tag 0x01030101, 65 bounded records, and different record sizes:
types 0/2/3/6 have lengths 704/2,128/1,840/1,904 respectively.

Reader accessors at 0x100eb6494 and 0x100eb6554 corroborate two dependency tables:
count fields +0x10/+0x14 and table-relative offsets +0x20/+0x24. Table addresses
are relative to header +0x5c's data base; entries are u64 offsets relative to
header +0x58's name base. All references resolve to exact NUL-delimited name
boundaries: 16 textures and 8 models. The first model is
`model_mothercrystal_001`; the first texture is **deff_mothercrystal_004**, distinct
from the inspector's texture 001. These are dependency lists, not model/texture
pairings. The parser explicitly rejects applying these table rules to tag 0x51.
No tutorial texture, timing or material has been silently substituted.

## Property recovery status and renderer implications

| Property | Status |
| --- | --- |
| Geometry, normals, UVs, original static texture | Retained from Phase 6C-1 |
| Primary record boundaries/raw types | Bounded and validated |
| Parent links | Consistent preorder candidate |
| Newer-format model/texture dependency tables | Reader-corroborated; tutorial only |
| Primary model/texture node bindings | Unknown |
| Transform/color/opacity constants vs curves | Unbound runtime clues only |
| Curve keys, time units, interpolation, lifetime | Unknown; no decoded segment |
| Coordinate spaces, projection, draw order | Unknown |
| Packed vertex attribute/material/shader semantics | Unknown |
| Blend/depth/cull/glow behavior | Unknown |

SceneKit can express ordinary transforms and opacity once verified curves and
coordinate/time conversions exist. A custom material or Metal may eventually be
needed for original shader combinations, packed attributes and particle batching.
The current evidence does not establish that Metal is necessary. There is no reason
to rewrite the renderer before recovering one node binding and one curve.
The inspector retains diagnostic Lambert lighting, camera and packed-RGBA mapping;
none is claimed to be the original BISHAMON appearance.

## Next step: Phase 6C-3

Trace the runtime initialization-context parameter pointer back to the compatible
serialized node, then decode one curve's pointer/count/key layout and evaluator.
Independently establish source time units and Global tag-0x51 conversion/schema.
Use the compatible tutorial only as a control. Before playback, tie a particular
model and property to exact offsets, keys, interpolation and lifetime; verify a
known-time still. Do not download a giant dataset or invent motion to bridge this
schema gap. Keep the production committed-result fallback unchanged.

## Validation completed — 2026-11-06

- 56 tests passed when run as separate suites, plus the Swift URLSession contract
  executable. Counts: BMB analysis 6, crystal/import 8, summon service 7, offline
  entry 6, unit content 8, artwork batches 10, summon UI assets 6, HTTP API 5.
  Unit content tests also ran the Swift exact-ID/name/rarity/PNG display check.
- A first combined unittest discovery attempt failed: backend process-global data
  roots conflict across modules, and the backend venv lacks build-time Pillow.
  Separate processes and the documented system-Python asset environment passed;
  this is not a claim that combined discovery is supported.
- Xcode 26.2 Debug Simulator and signed arm64 device builds succeeded. Both apps
  were updated in place, using the existing bundle ID. No uninstall occurred.
- Connected iPhone 16 Pro and Simulator both executed the static crystal diagnostic:
  960 vertices, 320 triangles; missing/corrupt content rejected; stop/restart and
  suspend/resume handlers passed. Both also executed the real embedded-backend
  UI diagnostic in separate UUID-named test campaigns: single, multi, duplicate
  submission prevention, insufficient-currency refusal, saved-result retention,
  11 decoded UI assets, missing-art fallback, four widths. The normal campaign
  was not used for these summons.
- Static viewport callback rates: phone 29.96/sec and Simulator 30.46/sec at the
  30 fps cap. Snapshot medians: phone 4.89 ms, Simulator 19.24 ms. Resident samples:
  phone 117,342,208 bytes; Simulator 124,637,184. These are static diagnostic
  measurements, not recovered-animation performance or isolated GPU memory.
- Restarted snapshot PNGs differed on both platforms. On the iPhone 154,746 of
  1,198,800 pixels differed (12.91%, maximum channel delta 229). Stop/restart state
  checks passed, but visual repeatability remains unresolved. No deterministic
  frame or animation-fidelity claim is made.
- CrystalPreview (189,566 bytes), UnitContent (1,089,195) and SummonUI (1,293,965)
  bundles are byte-identical to the retained Phase 6C-1 build. The signed Debug
  app is 42,157,413 bytes, the same measured size as Phase 6C-1.
- No normal campaign was copied, backed up, restored or deliberately modified.
  No new before/after save-byte comparison was performed in this phase. Save
  compatibility is covered by isolated test campaigns; actual user-campaign
  persistence across reboot remains a manual check.
- No runtime assets/network code, Swift UI or gameplay code changed in Phase 6C-2.
  No downloaded copyrighted files or generated resources were staged/committed.

## Build and manual device checks

```sh
cd ~/Documents/Projects/exvius-offline
python3 -B source/ios/content_tools/analyze_crystal_bmb.py
python3 -B source/ios/content_tools/import_crystal_preview.py

xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6C2-Simulator \
  CODE_SIGNING_ALLOWED=NO build

xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6C2-Device build
```

Existing Python runtime/content caches and local signing configuration are required,
as in Phase 6C-1. No project regeneration is necessary for the new analysis tools.
Run each Python test file in its own process: system `python3 -B` for
`test_crystal_analysis.py`, `test_crystal_preview.py`, `test_artwork_batches.py` and
`test_summon_ui_assets.py`; `source/ios/.venv/bin/python -B` for the other suites.

In Xcode open the existing project, select the existing team and iPhone 16 Pro,
and Run as an update with the unchanged bundle ID `com.example.ffberevival.dev`.
Never uninstall. Use launch argument `--crystal-preview` for the isolated inspector;
`--crystal-diagnostics` runs the static checks. Play must remain disabled.
Check Show/Stop/Restart and dragging, then Home-screen background/resume and
force-close/relaunch with Airplane Mode and Wi-Fi off. Remove diagnostic arguments
for normal play; verify your existing balance, collection and campaign after relaunch
and reboot. Do not summon merely to validate preservation. Actual radio-off,
Home-screen lifecycle and reboot checks were not automated here.

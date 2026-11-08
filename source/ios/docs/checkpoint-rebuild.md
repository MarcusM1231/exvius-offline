# Rebuilding the checkpoint through Phase 6D-4B

This checkpoint on `ios-port` preserves source, tests, project configuration,
research reports and small source/content manifests. Phase 4 offline Python,
Phase 5 names/static artwork and Phase 6B UI are already in its parent history;
this checkpoint adds the subsequent crystal/reveal/animation work and the explicit
Developer Lapis tool. It contains no original game payloads or executable runtimes.
The current library supports 417/423 target IDs plus two preserved research forms.
See [the final coverage report](unit-animation-expansion.md) for the six fallback
cases and indexed attack/magic/victory resources, which are not yet playback support.

## A source-only checkout is not a complete content backup

Xcode references `../.local/runtime/Python.xcframework`. That ignored dependency
must exist even for a Simulator build. The package phase also reads ignored local
content; it does not download assets during compilation or app launch. The default
build uses preservation `UnitContent` and original `SummonUI`; these are required
unless their explicit development fallbacks are selected. The other presentation
bundles are optional at packaging time and degrade to their documented controls,
static artwork or saved-results fallback. They are necessary to reproduce the full
accepted appearance. A clean checkout without private content will not reproduce
all visual features simply by opening Xcode.

| Dependency | Ignored local location | Setup/import and source identity |
|---|---|---|
| Python 3.13.11 Apple runtime | `.local/runtime/Python.xcframework` and runtime support files | `native/scripts/prepare_runtime.py`: pinned BeeWare 3.13-b13 archive URL/SHA; Python 3.12+ for safe extraction |
| Metadata / 423 static sprites | `.local/unit-content/sources`, `png-cache`, `versions` | `content_tools/content.lock.json`, `import_content.py --download`; bounded selected members, never full dataset |
| Original summon UI | `.local/phase6a`, `.local/summon-ui/versions` | `summon-ui.lock.json`, `import_summon_ui.py`; includes the privately recovered Global layout CPK and selected preservation textures |
| Original static crystal preview | `.local/phase6a`, `.local/phase6c1`, `.local/crystal-preview/versions` | `crystal-preview.lock.json`, `recover_crystal_dependencies.py`, `import_crystal_preview.py` |
| Layered crystal reconstruction | prior phase caches, `.local/phase6c3`, `.local/crystal-reconstruction/versions` | `crystal-reconstruction.lock.json`, `recover_crystal_reconstruction.py`, `import_crystal_reconstruction.py` |
| TOUCH SCREEN / cloud entrance | `.local/phase6d3a`, earlier texture cache, `.local/crystal-entrance/versions` | `crystal-entrance*.lock.json`, `recover_crystal_entrance.py`, `import_crystal_entrance.py` |
| Reveal research / production reveal cells | `.local/phase6a`, `.local/phase6d1/versions`, `.local/character-reveal/versions` | `reveal-stage.lock.json`, `reveal-research.lock.json`, `character-reveal.lock.json`, `recover_reveal_stage.py`, `import_reveal_research.py`, `import_character_reveal.py` |
| Original four animation samples | `.local/phase6d1/maria`, `.local/phase6d4/sources` | `reveal-unit-research.lock.json`, `unit-animation-sources.lock.json`, `recover_reveal_unit.py`, `recover_unit_animations.py` |
| Expanded animation library | `.local/phase6d4b/sources`, `.local/unit-animations/versions` | `unit-animation-expanded.lock.json`, `expand_unit_animations.py --restore`, `import_unit_animations.py` |
| Pinned CPK discovery indexes | `.local/unit-content/discovery` and phase-specific discovery directories | SHA-pinned index paths in the locks; existing bounded index reader is `expand_artwork.read_index` |

All locations above are relative to `source/ios`. Each importer derives its
versioned output from the corresponding lock digest. A manifest pins filenames,
resource bounds and checksums, not the original PNG, CSV, M3R, BMB or archive bytes.
The expanded animation lock is about 1.06 MB of JSON: 32 source/index descriptors,
1,270 member identities and 422 recovered exact-ID entries. It contains no sprite
pixels, frame compositions, animation payloads or embedded archives. Research JSON
in docs records counts, bounds, offsets and findings; it does not contain mesh
vertex/index buffers or shader payloads. Global-targeted preservation provenance
is not a claim of byte-identical original retail Global CDN bytes.

Private original IPA-derived layouts and some earlier research inputs cannot be
recreated from these source files alone. Use the matching already-recovered cache
or selectively recover the exact privately owned source members described in
[crystal recovery](crystal-recovery.md), [character recovery](character-reveal-recovery.md)
and [the summon UI guide](summon-interface.md). Preserve source identity and version
separation. Do not substitute JP/Memorial assets just to satisfy a missing filename.
A missing source or changed checksum should be investigated, not bypassed.

## Build with the existing content on this Mac

No recovery/download is needed when verified caches are present. These commands
regenerate build content; do not run them over locally edited content. Importers
validate locked identities and generally refuse changed outputs. Keep the ignored
cache intact. Follow phase guides when an input needs recovery.

```sh
cd ~/Documents/Projects/exvius-offline
git branch --show-current  # ios-port
# One-time runtime setup if missing (requires internet on the build Mac):
python3.12 source/ios/native/scripts/prepare_runtime.py
# Use the existing research environment with Pillow for content assembly:
python3 source/ios/content_tools/import_content.py
python3 source/ios/content_tools/import_summon_ui.py
python3 source/ios/content_tools/import_crystal_preview.py
python3 source/ios/content_tools/import_crystal_reconstruction.py
python3 source/ios/content_tools/import_crystal_entrance.py
python3 source/ios/content_tools/import_reveal_research.py
python3 source/ios/content_tools/import_character_reveal.py
python3 source/ios/content_tools/import_unit_animations.py
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -configuration Debug -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath /private/tmp/FFBERevival-Checkpoint CODE_SIGNING_ALLOWED=NO build
```

If metadata/static artwork is absent, `import_content.py --download` retrieves
only the pinned necessary members. For expanded animations, retain/recover the
pinned discovery indexes first, then invoke `expand_unit_animations.py --restore`
in capped batches until it reports zero restored members; import afterward.
See [animation expansion](unit-animation-expansion.md) for exact bounds, resume
behavior and the recovery limitations. These are build-time network operations;
the installed app's default backend and imported content remain fully offline.

Pillow is only a build/research dependency. Xcode's Python packaging process and
embedded gameplay do not need it. Follow `requirements-smoke.txt` for the desktop
backend smoke environment, and use Python 3.12+ for runtime archive preparation.
Tests that assemble real game content require the matching ignored caches. Run
`test_*.py` suites in separate Python processes: the legacy backend environment
and offline audit hooks are intentionally process-global. HTTP regression tests
require local loopback sockets; native smoke tests require Xcode command-line tools.

## Signing, saves and continuation

`native/Build.xcconfig` keeps `com.example.ffberevival.dev` and optionally includes
ignored `native/Signing.local.xcconfig`. Configure the local team there; do not
commit it, provisioning profiles, certificates or private keys. Device builds use
`-sdk iphoneos -destination 'generic/platform=iOS'` and existing local signing.
A team identifier is not an interpreter/framework dependency. No personal signing
values are stored in this checkpoint's generated project.

Normal saves live on the iPhone in Application Support under
`FFBERevival/offline-demo-v1/campaign.json`, outside the read-only bundle. They are
not a Git dependency and are not included. Keep the bundle ID and update in place;
never uninstall, replace or restore the campaign to rebuild a checkout. Diagnostic
campaigns are separate under `FFBERevival/validation`. No phone operation is needed
for this Git checkpoint.

All original game assets, generated animation bundles, IPAs/APKs/CPKs, archives,
`.local`, `.venv`, builds, diagnostics captures, signing inputs and saves remain
outside this commit. Two existing `.DS_Store` files at repository root and `source/`
are deliberately left untouched and unstaged. No full backup is created: Git alone
cannot restore ignored content. Existing local caches and the installed app are
preserved for Phase 6D-4C; its implementation has not begun in this checkpoint.

The standalone `inspect_reveal_research.py` research helper currently pins this
Mac’s absolute checkout path. It is not an Xcode/runtime dependency; review its
root path before using it on another Mac. Other original client locations recorded
in research reports are provenance references, not files supplied by Git.

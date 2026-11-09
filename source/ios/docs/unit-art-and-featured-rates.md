# Phase 7D — Exact-form static artwork and configured summon rates

## Outcome

Static artwork expands from **426/844** possible reward IDs to **839/844 (99.41%)**. **413 newly recovered exact-ID original static PNGs** are bundled, including all **105 missing 4★ forms**, 44 3★, 232 5★, 19 2★ and 13 1★ forms. No derived idle frames, fabricated art or same-name substitutions were used. The original animation library is unchanged and remains preferred by the existing OBTAINED renderer; static artwork is its fallback.

All **248 playable banners and 488 enabled offers** have analytic pool reports. Every configured featured ID resolves to an eligible exact form; no demonstrated pool/offer mismatch required changing a configured rate or reward. The original Python RNG, banner source definitions, costs, guarantees and save schema are unchanged. Rate details now show the actual configured probability and guarantee effects, rather than relying on the promotional image or a successful transaction as evidence of correctness.

## Phase 7C checkpoint and preservation gate

Commit **`82096c0cf349c26cb5577e3e36f3bba868c02645`**, `feat(ios): expand offline summon catalog and banner artwork`, contains 29 reviewed source/test/documentation/lock files. All 156 Phase 7C tests across 22 suites and the Swift HTTP contract passed before committing. UTF-8, JSON/Python parsing, staged-diff, binary and credential-pattern checks passed. `.DS_Store` files remained unstaged. No artwork, archives, campaigns or signing material was committed.

Verified incremental backup: **`/Users/marcusmoore/Desktop/FFBE Revive/Post-7C-Backup/`**. It copied 1,313 resource/report files (222,950,091 bytes), verified 1,317 files with SHA-256, and totals **400,529,599 bytes** including Git/restoration material. Zero checksum failures. It preserves all `.local/phase7c` resources, manifests, journals, reports and a complete standalone Git bundle, and depends on the unchanged `Post-7B-Backup` plus its two Phase 6 predecessors. No normal/HTTP/validation campaign saves, signing files, generated app bundles or unrelated files were included. External original IPAs and large preservation archives are retained separately as recorded in earlier inventories; cached resources suffice to reproduce the current checkpoint.

A separate restoration at `/private/tmp/FFBE-Post7C-Restore` verified the source commit, Git fsck, prior 13 content receipts and three Phase 7C receipts. Its fresh Simulator build passed. The new backup and all predecessors are sealed; Phase 7D resources are intentionally outside them. These same-disk backups do not protect against disk loss. See `Backup-Verification.json` and the backup's `README.md`/`restore_7c.py`.

## Artwork inventory, recovery and provenance

`Unit-Art-Coverage.json` and CSV account for all 844 reward IDs with English names, base/current/max rarities, banner frequency, prior/static/animation status, exact archive members, source dimensions/visible bounds and SHA-256 identities. The initial 418 missing forms comprised 105 4★, 237 5★, 44 3★, 19 2★ and 13 1★ forms. Most were present in indexed containers but had not been imported when the production reward set expanded beyond the older 423-unit target library.

The initial cached-index scan located 414 of those missing IDs. Checking the complete pinned list of 36 common unit containers found three additional tutorial forms. A further English unit CPK was inspected separately (one member, no remaining-form match), giving 37 inspected unit containers overall. All eleven outer ZIP indexes were searched for relevant unit paths. Limit-burst movie containers were not downloaded as substitutes for static sprites. Five newly encountered index files were isolated under `.local/phase7d/unit-art/discovery`; all earlier index bytes remain unchanged. This matters because the older animation recovery tool discovers candidate sources from its original index directory. The isolation prevents static research from altering its paused workflow.

`expanded_unit_art.py` reuses the bounded range reader and CPK table reader. Stored member names must match `unit_ills_<exactID>.png`; source indexes are SHA-pinned, offsets/sizes must remain inside their stored CPK and ZIP, and stored/decompressed identities are recorded separately. Supported CRILAYLA is decoded with the existing bounded decoder; unsupported encodings are rejected. PNG signature/chunks/CRC/decompression bounds, decoded dimensions, nonempty alpha bounds and transparent pixels are verified before import. All original source pixels and proportions are retained. The reported source rectangle is the alpha-visible bounding box, not an invented crop.

Recovery proceeds through validated 25-form checkpoints, reuses cached bytes, requires exact HTTP 206 ranges, throttles requests and stops on transport/range/rate-limit failures. Individual unsupported images are preserved in the ignored rejected-source directory and excluded from import. No entire preservation archive or dataset was downloaded. A clean resume uses pinned cache bytes; it does not silently change an existing lock or overwrite mismatched source files.

The 413 additions contain **412 unique decoded PNG byte sequences**, deduplicated in a **785,425-byte** content-addressed bundle including its catalog and receipt. Cross-ID byte equality is deduplication, not permission to assign another form's image. Each ID still has its independently verified source member. Original sources are retained unchanged in ignored storage. New sprites come from **Global-targeted preservation containers**; this is not proof of byte-for-byte original retail Global CDN provenance. No Memorial assets were imported. Original Global and Memorial cached CPK filename tables were searched separately for unresolved forms; results are in `Client-Static-Search.json`.

### Five remaining exact forms

| Exact master ID | Name | Rarity | Reason |
|---|---|---:|---|
| `100014405` | Reberta (JP) | 5★ | No exact static member found in the inspected unit containers or cached client tables. The metadata label is not authority to substitute a Global Reberta form or a Memorial/JP sprite. |
| `206003005` | Moogle of Narshe Mog | 5★ | Exact indexed member returned unsupported stored data; no validated PNG/CRILAYLA output. |
| `206003105` | Yeti of Narshe Umaro | 5★ | Same unsupported encoding/decoded-size restriction. |
| `207002505` | Avalanche's Biggs & Wedge | 5★ | Same unsupported encoding/decoded-size restriction. |
| `210001105` | High Summoner Braska | 5★ | Same unsupported encoding/decoded-size restriction. |

The four unsupported members are in `data-006`, `Ver0_unit22.cpk`. The ZIP filename, stored CPK magic and payload offset were independently rechecked against the cached index; the offsets agree. Their stored hashes and raw bytes are retained for research. They are **found but unsupported**, not described as permanently lost or proven corrupt. Reberta is **searched but not found within these sources**. No extra idle/action recovery was started. Existing cached animation coverage does not provide these exact forms with a validated fallback frame.

## Runtime artwork behavior

The primary 423-ID bundle and the three Phase 7C supplemental files remain untouched. `ExpandedUnitArt` is a separate versioned supplement integrated into the existing exact-ID catalog lookup. Its lock/catalog/image hashes are checked; names, family IDs and base forms are never lookup aliases. Content-addressed image filenames allow deduplication. Runtime access is local only.

Image loading remains lazy. Decoded static rows use an NSCache with a 64-image/8 MiB cost target; verified supplemental URL caching is limited to 64 entries. Cache targets are advisory, not hard process memory ceilings. Nearest-neighbor scaling and existing transparent-pixel anchoring remain in use. The established attack → idle → static preference and original Global menu/reveal components are retained. Missing assets retain explicit placeholders and do not block valid inventory transactions.

Developer → **Expanded exact-form sprite gallery**, or `--expanded-unit-art-check`, provides a searchable read-only view and an explicitly labeled OBTAINED asset preview. These previews never initialize a summon backend, spend currency, create inventory or access campaign saves. Their preview identities are UI fixtures only; production still requires the validated immutable committed receipt. The diagnostic decodes all available sprites and renders representative new 3★/4★/5★ forms, plus the Shadow/Rakshasa regressions. It also samples 120 row renders for memory observations.

## Pool and featured-rate audit

`audit_summon_rates.py` reads the source-pinned expanded catalog into a temporary isolated service without buying anything. `Banner-Pool-Audit.json` records each banner's source file/evidence, configured pool, every offer, actual normalized per-form probabilities, weights, guarantees and effective distributions. `Featured-Rates.json`/CSV contain **1,882 featured offer/unit records covering 554 distinct IDs**.

Claims are kept separate:

- Artwork identity follows exact definition filenames and prior preservation locks. Promotional artwork alone is not an independent unit-ID/rate table.
- Featured metadata comes from explicit tier lists and community `unit_ids`, including the legacy engine's implicit top-tier share rule.
- Actual eligibility and awarded rarity come from the existing Python expanded pool/master data, including guaranteed pools.
- Rate weighting comes from explicit row weights or tier/featured-share configuration. The audit records both mechanisms.
- A displayed within-rarity boost compares against equal probabilities for the **same eligible forms and actual rarity mass**. It is a defined counterfactual, not an asserted original off-banner rate or historical control banner.
- Historical verification is a separate evidence claim; no authoritative numeric historical rates were established here.

There are **1,776 offer/unit records above the equal-chance rarity baseline**, and **106 not above it**. The UI does not automatically label every featured character rate-up. All configured featured forms were eligible; no enabled offer had a configured pool or guaranteed-slot override that the legacy engine ignored. Unsupported ticket, step-up, NV, box, selection and mixed-reward families remain unavailable as in Phase 7C. No extra banners or rates were activated as a side effect of this audit.

Analytic calculation mirrors the engine's actual behavior. Independent guaranteed slots use their own normalized pools and combine per-slot expected counts and `1 − product(1 − p)` occurrence probabilities. Legacy rarity guarantees without a slot count use a different rule: only if all draws miss the rarity floor, the first minimum-rarity award is replaced. The model explicitly accounts for the replacement's removed-unit distribution and replacement probability. A guarantee pool without an explicit count follows what the legacy implementation actually reads; the audit does not silently pretend a different pool is used. Future fixed-unit/combined guarantee shapes fail clearly until modeled. No enabled offer needed that unsupported model.

The tests enumerate every RNG branch of small real-engine fixtures for both guarantee behaviors and compare expected counts and at-least-one probabilities with the analytic projection. All 488 offer distributions normalize; expected award counts equal their actual draw counts. No Monte Carlo sample is presented as exact probability evidence. Computation uses the same floating-point configured weights as Python, with normal numerical tolerances.

### Historical evidence and limits

A [contemporaneous July 2016 community thread](https://www.reddit.com/r/FFBraveExvius/comments/4rtv1p/global_kefkagolbezchizuru_gacha_megathread/) corroborates the Kefka/Golbez/Chizuru event and a 500-Lapis single/ticket option. Its informal pull estimates are not published server odds and were not used to replace configuration. It does not prove the offline guaranteed-Chizuru multi offer. A [Charlotte event reference](https://www.reddit.com/r/FFBraveExvius/comments/c9bgzj) was visible in search, but direct retrieval failed; it establishes no exact rate here. Local recovered promotional images corroborate visual offers, but do not establish every modern reconstructed pool or guarantee.

The report therefore marks all numeric rates as **offline configured rates, historical server rates unverified**. No rates were guessed from art, no historical percentage was fabricated, and no source probability was changed. Archive ID/name assignments can be revival-authored aliases rather than original server identities.

## Details screen and confirmed corrections

The Global-style layout is preserved. A collapsed **Drop Rates** section for each supported offer shows featured name, exact rarity, eligibility, base-draw probability, within-rarity weighting status, guarantee description, and (for multi offers) guarantee-adjusted average per draw and chance of at least one copy. Historical confidence notices are visible before purchase. Technical source paths/hashes stay in research artifacts.

The confirmed presentation gap was that the old featured list inspected explicit tier metadata only. Some valid banners use explicit weighted row lists or community featured IDs. The new read-only projection includes those configured IDs and computes the engine's effective values. No RNG or pool edits were needed. For banner 12, the configured single draw gives Chizuru `100004604` **2.565%**, Kefka `206001703` **12%**, and Golbez `204001403` **12%**; its configured 11-pull guarantees Chizuru. These are offline configuration facts, not claims of original 2016 server rates.

The existing character-reveal diagnostic now refreshes its quote before the next isolated purchase, matching the established stale-quote protection. Production purchases, immutable receipts, Continue/Skip All, rollback and save integrity remain unchanged.

## Build, test and device evidence

Final automated, build, memory, campaign and manual-test results are recorded in the companion machine-readable artifacts. Before/after screenshots include Ludmille 4★, newly recovered forms, actual OBTAINED/static fallback, rate details, and missing-form behavior. All purchase tests use isolated purple campaigns. No normal-campaign Lapis or tickets are spent.

All **168 tests across 24 isolated suites pass**, plus the Swift HTTP URLSession contract. The first animation-discovery run caught the new research indexes entering the older candidate set; after isolating those indexes, all 11 affected tests passed. Final artwork tests also prove cache-only resume, no repeated cached-index downloads, no animation-discovery changes, duplicate-ID rejection, corrupt output/source rejection, PNG/transparency bounds and deterministic output. The initial failing log and successful retest are retained rather than hidden.

Both final Simulator and signed arm64 iPhone builds passed; `codesign --verify --deep --strict` passed. The app was installed in place with the unchanged `com.example.ffberevival.dev` identifier. Simulator and device diagnostics decoded **839 exact sprites**, rendered representative recovered 3★/4★/5★ rows and Shadow/Rakshasa, and verified an unresolved exact form still has no fabricated artwork. Actual Simulator interaction confirmed recovered Ludmille 4★/5★ sprites, the static OBTAINED component and guarantee-adjusted rate details. Its real-backend presentation regression committed exactly two isolated purchases (one and eleven), preserved 9,500/4,500 test Lapis, finished every reveal once, retained save bytes during reveals, exercised corrupt/missing art and 40 resource-cleanup cycles, and passed cold recovery with zero new summon requests.

On the physical iPhone 16 Pro, the user confirmed recovered sprites are complete/correctly framed, recovered OBTAINED previews work in Airplane Mode with Wi-Fi off, and the rate details plus single/11 purchases show correct actual results/artwork with one 500 and one 5,000 test-Lapis charge. Offline artwork preview was manually tested in this phase; the new purchase checks were not specifically reported as being performed offline. Earlier Phase 7C offline purchases remain documented separately. No manual check is inferred from a build alone.

The normal campaign SHA-256 is identical before/after this phase: **`f6fd9a5b390480d91ba84d94da208e4a3c83d1ff22a31aa690e780f058438d3b`**. This is the fresh Phase 7D baseline; it need not equal an older phase's campaign hash after intervening legitimate play. Only previously authorized private `/private/tmp` exports were used, solely for comparison. No save contents are in these report artifacts or Git.

Uncompressed final app sizes: Simulator **194,342,220 bytes**; signed device **173,864,787 bytes**, an increase of **1,202,785 bytes** over Phase 7C. In 120 row-render samples, resident growth was **4,894,720 bytes on Simulator** and **8,798,208 bytes on iPhone**. These include renderer/runtime allocations and advisory cache behavior; they do not establish a hard memory ceiling or a long-duration leak guarantee. Machine-readable memory, size, sprite, transaction, cold-recovery and campaign reports accompany the screenshots and preview recording.


## Rebuild and preserve the private cache

Git deliberately contains no original artwork, IPAs, archives, animation bundles or signing material. The Phase 7C backup chain restores the previous milestone; additionally retain the complete ignored **`source/ios/.local/phase7d/`** directory for this phase, including its isolated CPK indexes, source/rejected bytes, coverage journals and versioned bundle. Source code/locks alone cannot reproduce proprietary images without private caches or bounded recovery from the recorded public preservation sources. Do not overwrite the sealed backups. A later authorized backup should preserve these new resources as a new checkpoint.

From the repository root after restoring the existing runtime and earlier bundles:

```sh
# Cache-only deterministic import; needs Pillow on the Mac for validation.
python3 source/ios/content_tools/expanded_unit_art.py
# If original sources/indexes are absent, bounded recovery only:
python3 source/ios/content_tools/expanded_unit_art.py --recover
# Read-only full configured-pool report; its campaign is temporary and isolated.
python3 source/ios/content_tools/audit_summon_rates.py
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj -scheme FFBERevival -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath /private/tmp/FFBERevival-Phase7D-Simulator CODE_SIGNING_ALLOWED=NO build
xcrun simctl install booted /private/tmp/FFBERevival-Phase7D-Simulator/Build/Products/Debug-iphonesimulator/FFBERevival.app
xcrun simctl launch booted com.example.ffberevival.dev --expanded-unit-art-check
```

The build verification import is stdlib-only; Pillow is used during recovery/import, not shipped to iOS. Existing Phase 7C metadata/banner import instructions still apply. Run each unittest module in a fresh process to avoid legacy global metadata caches, plus `python3 source/ios/tests/test_native_client.py` for the Swift HTTP contract. The production embedded backend remains the default; HTTP development mode is retained.

For the existing iPhone and ignored signing configuration/team:

```sh
xcodebuild -project source/ios/native/FFBERevival.xcodeproj -scheme FFBERevival -configuration Debug -sdk iphoneos -destination 'generic/platform=iOS' -derivedDataPath /private/tmp/FFBERevival-Phase7D-Device build
codesign --verify --deep --strict /private/tmp/FFBERevival-Phase7D-Device/Build/Products/Debug-iphoneos/FFBERevival.app
xcrun devicectl device install app --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 /private/tmp/FFBERevival-Phase7D-Device/Build/Products/Debug-iphoneos/FFBERevival.app
xcrun devicectl device process launch --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 --terminate-existing com.example.ffberevival.dev --expanded-unit-art-check
```

Never uninstall, restore a campaign or change the bundle identifier for this update. Use `--banner-menu-test --menu-banner 12` for isolated single/11 tests, and no diagnostic flags for the normal campaign. Verify recovered 3★/4★/5★ forms and Shadow/Rakshasa in the gallery, compare per-offer Drop Rates, test crystal → OBTAINED → results, Skip All, then offline playback with Airplane Mode/Wi-Fi off. Restore connectivity afterward if collecting the final private checksum report.

## Next phase

Investigate the four unsupported Ver0 static encodings with their retained exact source bytes; keep the Reberta JP form distinct until an exact verified source is found. Expand historical evidence per banner before claiming original numeric odds. Ticket/step-up/mixed-reward/vision-card presentation remains separate work with existing blockers. Missing-character animation/action recovery stays paused. Phase 7D remains uncommitted, with no push or upstream merge.

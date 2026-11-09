# Phase 7C — Expanded offline summon catalog

## Result

The original Global-style Phase 7B menu is retained. Of 471 browsable entries, **248 are playable (246 newly enabled)**: 238 Rare, 9 Limited and 1 Standard. There is no arbitrary activation cap. Every enabled definition passed exact master/name/pool checks and real Python transaction/save/reload validation for every declared offer. Python remains the sole reward and currency authority.

**467/471 entries (99.15%) have main artwork; 466 have a declared detail role.** This is exact repository-definition mapping, not proof that revival IDs are original Global server IDs. The 423-unit primary sprite library and original animation coverage remain intact. Three exact static forms were added separately after device feedback: Shadow `206000504`, Rakshasa `100004104`, `100004105`. Total bundled static artwork: **426 IDs**. These additions are not recovered animations.

## Protected checkpoint and restoration

Phase 7A/7B commit: `91aa90c5f0ee3bd32c6104ef4c836a7f8e239ff2` (`feat(ios): reconstruct original Global summon menu`). Its 136 tests passed before committing; reviewed content was source, tests, configuration, documentation and small content locks. No assets, saves or signing files were staged.

Incremental backup: `/Users/marcusmoore/Desktop/FFBE Revive/Post-7B-Backup/`. Verified size **249,958,946 bytes**, 277 SHA-256 manifest entries, zero failures. This preserves 272 resource/report files plus source/Git restoration material. It depends on the unchanged `Pre-6D-4C-Backup` and `Post-6D-4D-Backup` siblings. A separate temporary restoration verified Git, all base/delta hashes and 13 content receipts, restored Python, and built a fresh Simulator app successfully. See `Backup-Final-Verification.json` and `Backup-Restoration-Instructions.md` in the companion report directory. No campaign saves or credentials are included. All three backups are sealed and unchanged by Phase 7C.

Phase 7C changes remain uncommitted on `ios-port`. No push, upstream merge, app uninstall or save reset occurred.

## Exhaustive artwork classification

All eleven previously verified preservation ZIP indexes were scanned, including main, detail and additional panels. **542 candidates** were classified:

- 533 paths referenced by repository definitions, including 24 additional detail panels.
- 532 PNG source files recovered and validated; 531 unique image byte sequences after deduplication.
- 1 referenced image found but unsupported by the current 2 MB encoded-image bound: `data-001:static/gacha_community/art/translated/gacha_20200511_brave_ability_en.png`, 2,303,743 bytes. Its index entry is known; its body was not fetched or PNG-validated. It is not classified as lost.
- 9 unmatched namespace paths. Their bodies were not downloaded or assigned to banners by guessed character names. Exact paths and status appear in `Artwork-Classification.json`.

All relevant indexed candidates have a disposition; no indexed candidate is silently omitted. The search is exhaustive for these cached indexes, not for every original CDN file ever distributed. The four native IDs without exact recovered main art are `9300002`, `9300005`, `9300013`, `9300030`. Their placeholders mean searched but not recovered from these sources, not permanently lost. Complete per-entry names, categories, source definitions/digests, roles, dimensions, language evidence, archives, provenance, checksums, availability and reasons are in `Banner-Coverage.json` and CSV.

Recovered sources comprise **104 native English Global-targeted preservation paths and 428 community-calendar preservation paths**. They must not all be described as independently authenticated retail Global CDN bytes. The preservation set can include repaired or derived material. Community filename mappings and authored aliases are explicitly distinguished from original server identities. No Memorial/JP artwork was imported in this phase. Local English OCR examined all 532 images, corroborated Latin text in 520, with zero processing errors; it does not establish provenance or validate every word. Twelve non-detections are not invalid images.

Eleven cached original Global IPA CPK indexes were also searched. Relevant original layouts/font resources are documented in `Original-Global-IPA-Audit.json`; this did not identify an additional downloaded promotional-image collection. The original Global layout/UI resources remain separate from preservation banner illustrations.

## Recovery and bundle integrity

`banner_artwork_audit.py` inventories definitions and indexes. `recover_banner_library.py` uses bounded resumable HTTP 206 reads, ZIP local-header/name/size/method/CRC checks, decompression and image bounds, PNG decoding/dimensions and SHA-256. Reads are throttled at one-second intervals, coalesced to at most 1 MB, with a 4 MB batch budget. Unsupported ranges stop recovery. Verified cache files are reused. Public release links are recorded; temporary signed redirects are not stored.

Network payload recovered in this phase: **35,843,987 banner bytes**, **406,209 supplemental master bytes**, and **4,782 exact static-form bytes**. No full preservation archive or 14.6 GB dataset was downloaded.

`import_banner_library.py` deterministically creates content-addressed images and a strict receipt. The bundle maps 741 repository IDs including hidden aliases, with 1,505 logical ID/role references. This is broader than the 471 visible native entries. Main/detail roles can intentionally reference the same source image when the definition does so; 466 detail roles do not mean 466 distinct original detailed illustrations. Extra detail panels are ordered by original filename. Duplicate image bytes are shipped once.

BannerArt is **39,555,852 bytes**, including catalog/receipt (39,184,943 source-image bytes before deduplication). ExtraUnitArt is **5,689 bytes**. The expanded metadata directory is **9,963,944 bytes**. Locks record source identities and hashes, not copyrighted image data. Original PNGs, archives, converted bundles and caches remain ignored under `.local`.

Runtime pins the lock/catalog and verifies exact image identity. Lazy detail loading and ImageIO downsampling avoid decoding the whole library at launch. The cache targets 16 images/12 MiB decoded cost; NSCache limits are advisory. Decode dimensions are bounded to 1024, source dimensions to 4096 and encoded files to 2 MB. Aspect ratios are retained. Missing/corrupt images fall back visibly without affecting purchase eligibility.

`import_extra_unit_art.py` is a separate small exact-ID supplement. It checks original CPK index SHA, exact member row/name/offset/bounds, transparency/PNG integrity and locked file SHA. It never substitutes another rarity form by name. The older primary sprite and animation locks are unchanged.

## Metadata, eligibility and gameplay behavior

The full recovered unit table contains **3,311 master rows**, with **3,089 named unit IDs** (3,095 English text rows include six non-unit keys). This metadata was already present in the unit display catalog; the old backend fixture exposed only 423 synthetic records. Expanded summon metadata now uses preserved unit/name/awakening rows plus real supplemental ticket (17), important-item (606), item (4,729), and limit-burst (3,584) tables. Across enabled banners there are **844 distinct possible reward IDs**, all with verified master rows and nonempty English names.

These are summon/inventory metadata, not a complete battle/progression database. Unneeded tables retain empty fixture scaffolding. The generated legacy `synthetic-metadata.json` marker describes that original scaffolding; it is not a claim that the replaced, locked master tables are fabricated. The catalog-policy/locks explicitly identify the recovered tables. No 14 MB limit-burst-level table was needed or downloaded.

Eligibility is automated by `banner_eligibility.py` and `build_summon_catalog.py`. It checks finite positive original Python pool weights, names/master records, supported draw counts/currencies, guarantees, reward shapes, inventory creation, exact currency deductions and save/reload equivalence. Unsupported extra rewards fail the whole banner rather than being dropped. All 471 entries have audit records in `Eligibility-Full.json`; the exact enabled list is in `Enabled-Banners.json`, and the 246 additions in `Newly-Enabled-IDs.txt`.

The existing `PlayerState.roll_gacha()` and source banner JSONs are unchanged by Phase 7C. The two previously playable pools (`49`, `9100203`), per-unit weights, awarded rarities, costs (500/5000) and guarantees match the old fixture exactly. Newly enabled generic definitions expand against the full recovered metadata using the existing engine's name filtering. They are offline reconstruction definitions, not verified historical server rates or date-filtered historical rosters. Displayed rarity probabilities are normalized from the actual Python base pool; guaranteed slots can change final draw distributions. Historical artwork may advertise unavailable features, and details clearly state that only the offered offline unit rewards are implemented.

Metadata and engine-source hashes are checked before opening campaigns. Existing owned rows are preserved verbatim: the legacy loader would otherwise normalize old fixture LB levels when real LB metadata became available. An explicit compatibility test catches this and confirms startup does not rewrite the save. New grants use recovered metadata. No save-schema reset or normal-campaign migration was performed.

Quotes carry opaque SHA-256 tokens binding definition, offer, balance and relevant banner/step/usage state. Python re-quotes under its transaction lock and rejects stale tokens before rolling. Swift forwards the token and receives one immutable committed receipt. Animations, Continue and Skip All consume that receipt; they do not roll or charge again. New banners require tokens; the two original offers retain compatible legacy requests. There is no automatic uncertain-transaction retry. HTTP development mode retains its existing API and also accepts quote tokens.

## Unsupported families

Ticket foundation is implemented/tested in the real engine using recovered ticket/group/item IDs, quantities, floors, consumption, insufficient tickets and save/reload. Native ticket selection/inventory request presentation is not complete, so affected offers stay disabled; no Lapis substitute or false Free label is used.

All **13 step-up definitions** were audited and remain disabled. Their blockers include unsupported bonus rewards, ticket adapters, missing metadata and unsupported pools. A deterministic two-step engine fixture verifies step-specific pools/costs/draws, wrap/lap and persistence. This does not establish production step-up support. No step-up bonus is silently skipped and no speculative step-up purchase UI is enabled.

NV/7-rarity pools requiring unsupported vision-card/reveal handling, mixed rewards, boxes and selection adapters are conservatively disabled. There are 184 entries with unsupported high-rarity dependencies; reasons can overlap. Some definitions with otherwise valid primary offers remain disabled because their secondary/bonus behavior is incomplete. This is deliberate whole-definition validation, not a temporary arbitrary banner count limit. Free/friend/limited offers are enabled only when the same complete unit-only transaction checks pass.

## UI and validation

Phase 7B tabs, backgrounds, gold buttons, image frames, confirmations and crystal → OBTAINED → results flow are retained. Necessary additions are lazy additional detail panels, accurate non-Lapis labels and a historical-artwork notice. Existing original layout conversion is unchanged. No animation-recovery research was resumed.

Simulator interaction used an isolated purple campaign. Banner 12 single committed 500 Lapis and displayed one actual Russell reward; an eleven pull committed 5,000 once, Skip All showed all eleven actual rewards, and navigation did not purchase again. Rare/Standard/Limited, unavailable step-up, missing artwork and screen-size captures accompany this report. A recording shows the actual new-banner flow. The `--menu-banner` diagnostic can force a selected detail on fresh presentation; it is not a production navigation preference write.

The signed arm64 build was installed in place on the iPhone 16 Pro. The user confirmed new banner 12's single result and 500 charge, and that summons work with Airplane Mode/Wi-Fi off. They identified missing Shadow/Rakshasa results art; exact higher-rarity static forms were recovered and installed. On-device diagnostics decoded all 426 images and rendered all three new forms; the user confirmed all three appear correctly. No additional random summons were required for that check.

Normal campaign SHA-256 before/after is identical: `386f167b5233b3a0707226a1f88ccd022394039060d4319ae76d81a7b985f09a`. Only explicitly authorized private `/private/tmp` exports were used; report artifacts contain hashes, not save contents. All purchase tests used isolated accounts.

Memory samples for 120 sequential banner decode requests: Simulator resident increase ~1.87 MiB; iPhone ~3 MiB. See machine-readable reports for before/peak/after values. This bounded sample is not a long-duration leak guarantee. All **156 tests across 22 isolated suites passed**, plus the separate Swift HTTP URLSession contract. Uncompressed app sizes: Simulator **193,029,653 bytes**; signed device **172,662,002 bytes** (about 164.7 MiB), a **46,367,745-byte** increase over the Phase 7B device build. `Build-Sizes.json` and `Tests/Results.json` provide machine-readable evidence. Signed build, codesign and Simulator execution passed.

## Rebuild and local dependencies

A clean checkout requires the private recovered resources/Python runtime; Git alone deliberately does not contain copyrighted content. Restore the sealed Phase 7B backup chain for the older milestone. Current Phase 7C `.local/phase7c`, referenced earlier unit-content/discovery caches and all pinned source indexes must additionally be preserved for offline recreation. The sealed old backup intentionally does not include these new resources. Back up the new ignored cache separately when requested; do not overwrite prior checkpoints.

From the repository root, after restoring earlier runtime/content and source-index caches:

```sh
python3 source/ios/content_tools/recover_banner_library.py
python3 source/ios/content_tools/import_banner_library.py
python3 source/ios/content_tools/recover_summon_masters.py
python3 source/ios/content_tools/build_summon_catalog.py
python3 source/ios/content_tools/import_extra_unit_art.py
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj -scheme FFBERevival -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath /private/tmp/FFBERevival-Phase7C-Simulator CODE_SIGNING_ALLOWED=NO build
xcrun simctl install booted /private/tmp/FFBERevival-Phase7C-Simulator/Build/Products/Debug-iphonesimulator/FFBERevival.app
xcrun simctl launch booted com.example.ffberevival.dev --banner-menu-test
```

The recovery commands resume bounded retrieval only for missing verified source members; a complete verified cache uses no network. They do not implement a `--help` CLI. `build_summon_catalog.py` must run in its own process because Python metadata engines cache tables. It reproduces and verifies the existing source lock rather than silently replacing it. All build-time packaging verifies pinned receipts. The extra form importer accepts `--download` only for missing source PNGs.

For the existing phone, preserve the ignored local signing configuration/team and bundle identifier:

```sh
xcodebuild -project source/ios/native/FFBERevival.xcodeproj -scheme FFBERevival -configuration Debug -sdk iphoneos -destination 'generic/platform=iOS' -derivedDataPath /private/tmp/FFBERevival-Phase7C-Device build
codesign --verify --deep --strict /private/tmp/FFBERevival-Phase7C-Device/Build/Products/Debug-iphoneos/FFBERevival.app
xcrun devicectl device install app --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 /private/tmp/FFBERevival-Phase7C-Device/Build/Products/Debug-iphoneos/FFBERevival.app
xcrun devicectl device process launch --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 --terminate-existing com.example.ffberevival.dev --banner-menu-test --menu-banner 12
```

Never uninstall. Normal launch without diagnostic flags uses the existing campaign. `--extra-unit-art-check` is a read-only form gallery. `--banner-art-missing` exercises safe missing-art presentation. To run regressions, run each `source/ios/tests/test_*.py` unittest module in a fresh process (excluding the separate `test_native_client.py` HTTP/Swift runner), then run that native-client script. Separate processes prevent engine fixture caches from contaminating unrelated suites.

## Next phase

Prioritize exact static fallback coverage for the wider 844-ID reward set without restarting missing-animation recovery. Units with verified names/master records can be awarded and displayed with a clear missing-art placeholder, but many expanded forms still lack art. Of the 844 reward IDs, **426 have exact static art and 418 lack exact static art**; `Reward-Art-Coverage.json` lists those remaining forms. No same-name substitution is permitted. Then implement typed native ticket selection and full mixed-reward/vision-card receipts before activating those families. Step-ups require complete bonus, reset/limit and presentation validation; boxes/selection need dedicated adapters. Recover the known oversized image with a reviewed bounded path if needed. Keep production rewards separate from presentation and preserve old backups.

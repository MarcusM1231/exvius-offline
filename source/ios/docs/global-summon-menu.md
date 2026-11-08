# Phase 7B — Original Global summon menu

## Result and scope

The production Summon tab now uses recovered Global-style tabs, common/header frames, banner images and original gold single/eleven buttons. Banner browsing, details, live quote confirmation and the existing committed crystal → attack/idle OBTAINED → results pipeline are connected. There is no new RNG or reward generator.

Only banners `49` and `9100203` are enabled in the embedded production campaign. Each retains its existing 500-Lapis single and 5,000-Lapis eleven offer, real Python pool and guarantees. The native catalog contains 471 browsable records: the 469 archive-visible definitions plus the two validated authored demo definitions which archive alias deduplication otherwise hides. The remaining 469 records are unavailable for native purchases. This is a small production menu reconstruction, not activation of the entire historical game.

Work remains on `ios-port`, based on checkpoint `6da00ff0f2700428b7950c8dae3fd5140fcbf7c3`. Phase 7A research and locks were preserved. No commit, push, merge, reset or clean was performed. Both verified Phase 6 backups were left untouched. No original Android files changed. The only shared gameplay changes are the two specifically requested upstream pool corrections described below. The installed app retains `com.example.ffberevival.dev` and was updated in place without uninstalling or restoring a save.

## Original resources and authenticity

`global-menu-ui.lock.json` independently pins the selected original Global 9.1.0 common/header CPK members and the previously verified English preservation gacha textures. It does not replace the Phase 6 `summon-ui.lock.json` or Phase 7A research locks.

The 24 selected UI images include:

- Original Global `common.cpk` common atlas button skins (`button_mini_long1/2` and `button_middle1/2`), header decoration and background, Lapis icon and window texture.
- Verified Global-targeted preservation Rare / Standard / Limited tab states and tab background, gacha backgrounds and unit plate.
- Original English single / eleven summon button artwork and pressed variants from the previously recovered `Ver58_gacha1` resources.
- The original top/detail/result/confirmation/left/right layout CSVs already pinned in Phase 6B; the full Phase 7A comparison preserves the tab, ticket and step-up layout research. No ticket/step/box purchase screen is activated here.

The original CSV anchors remain the reference: top tabs at y250, list/banner origin y338, main banner 640×160; detail banner x0/y250/640×392; left button x2/y653/304×136 and right button x332/y653/304×136. The implementation uses width-relative image ratios, the two original 304-wide button footprints within 320-wide columns, and the original 640-wide reference region. Original asset frames are decoded with the existing TexturePacker handling for rotation, trimming and source canvases.

The view does not stretch a whole 640×1136 screen to modern dimensions. SwiftUI supplies the safe area; the compact account/header region is adapted because this port does not implement the original full account HUD. Banner width is capped at 640 points; image aspect ratios are preserved, tabs have a minimum 44-point touch height, and long details scroll vertically. Buttons remain inside safe-area content. At very narrow widths, the minimum tab touch height intentionally adds a few points beyond strictly scaled original heights. Left/right button columns slightly redistribute spacing for native touch layout. Original pixel textures and unit art use nearest-neighbor interpolation.

Known fidelity gaps: the exact original English general font mapping remains unresolved, so text uses system serif/readable native typography. Account HUD fields that do not exist in this port are omitted. Details text, unavailable messages, archive filter and confirmation text layout are adaptations within original skins. The top Archive/Results toolbar is an adaptation, not a claim of original Global control placement. Historical banner art can advertise options not implemented here; image lettering never authorizes a purchase. The original result grid remains its existing documented adaptive reconstruction. This is recognizable original-style presentation, not a claim of pixel-perfect reproduction.

No Memorial imagery is silently substituted. The Developer browser remains a separate read-only Phase 7A snapshot, including its original provenance and historical issue notes. Its archive-adjusted classification is distinct from the native menu's original base wire categories.

## Artwork coverage and bounded recovery

46 PNGs cover **24 exact banner IDs**, including both enabled banners and nine permanent/common families. Of these, 44 English native main/detail images cover 22 IDs; the two demo banner images are separately labeled community-calendar preservation images. Both demo detail screens use their exact-ID list banner because an individually verified original detail image is unavailable. They preserve the 640×160 aspect ratio rather than stretching it to the detail region's 640×392.

Coverage in the 471-entry native menu is 24 illustrated / 447 missing. Missing art uses an explicit banner placeholder with the actual metadata name. There are no character-name or similarly named banner substitutions. See `Artwork-Coverage.json` for exact IDs and missing-ID list.

The recovery process reused pinned ZIP indexes and fetched only selected loose PNG members. The first expansion transferred 1,702,508 bytes, and the permanent/common expansion transferred 1,313,291 bytes: **3,015,799 new bytes** total. Existing six-image Phase 7A content was reused. No full dataset or CPK was downloaded. `RangeClient` enforces exact HTTP 206 Content-Range and byte counts, bounded per-request/total budgets, rate limiting, and stops on unsupported ranges or rate limiting. ZIP local headers, exact filenames, decompression bounds, indexed size/CRC, PNG decode and dimensions are validated.

Where existing definition metadata already supplied SHA-256, it was checked. Permanent images lacked that prior pin: their first import was verified against the already pinned archive index, exact local member name and CRC, then the observed SHA-256 was recorded. This is reproducible identity evidence, not publisher attestation. Subsequent recovery checks the recorded SHA. Global-targeted preservation does not establish byte-for-byte retail Global CDN provenance.

Versioned bundles: `BannerArt` 3,419,149 bytes; `GlobalMenu` 1,442,614 bytes. Incremental uncompressed resource footprint is **4,861,763 bytes** (about 4.64 MiB), excluding minor source/code changes and any IPA compression. The full research JSON is not added to the application. Exact-ID PNG loading is lazy and uses a 16-image / 12-MiB decoded-image NSCache. No runtime image download exists.

Private content lives under ignored `.local/phase7b`, `.local/global-menu` and the pre-existing `.local/phase6a` / `.local/phase7a`. No artwork, archive, IPA, extracted binary, save or signing credential is added to Git. Preserve these directories privately alongside both Phase 6 backups if retaining the exact expanded cache; neither sealed backup was changed in this phase.

## Read-only Python catalog and quote boundary

`prototype/banner_menu.py` adds `MenuSummonService` on top of the existing `SummonService`. `menu()` and `quote(banner_id, offer)` hold the facade lock and only inspect definitions and stored campaign values. They do not call `roll_gacha`, `banner_state`, `gacha_archive.menu`, currency mutation or save. The definition cache is not campaign data. All returned DTOs are detached projections.

Embedded operations `menu` and `quote` use the existing serial Python worker. HTTP development equivalents are GET `/v1/menu` and `/v1/quote?banner_id=49&offer=secondary`. Existing `/v1/banners`, state and summon APIs remain available. Full-data HTTP development retains its prior legacy summon capabilities; the new native menu still enables only the validated IDs, and embedded iOS always uses the existing demo metadata mode.

Catalog fields include exact ID/name, base original-client category, secondary archive-group membership, featured IDs, definition rate weights/notices, description where available, supported state and offers. Quotes include stable primary/secondary offer identifier, source detail ID, draw count, typed cost, balance, eligibility/reason, guarantee description/slot data, ticket group and available ticket inventory, current step/lap, usage and purchase limits. Unknown ticket master data is displayed as unavailable; ticket-only rows are not mislabeled Free. Unsupported offer families never become executable simply because they have definitions or artwork.

The production native catalog uses base original-client wire categories: 455 Rare, six Standard and ten Limited entries in this snapshot. Phase 7A's broader archive-adjusted wire categories intentionally differ. Season 1–4 / Collaborations are retained only through the secondary Archive filter. Filters, search and navigation are Swift view state, not saved campaign archive preferences.

At confirmation, Swift requests a new Python quote and displays its authoritative price/eligibility. It never derives costs or guarantee rules. The transaction facade checks eligibility again under its lock immediately before delegating to the existing roll/save/rollback transaction. Only one request can be pending in `SummonModel`. Unknown/stale offer names and unsupported embedded banner IDs fail before a roll. There is no automatic transaction retry. The immutable correlated committed receipt still owns the reveal; animation, Continue, Skip All and menu navigation do not issue purchases.

## Supported and unavailable families

| Family | This phase |
|---|---|
| Two authored production Lapis banners | Live Python quote, single and eleven confirmation, original buttons, existing transaction/reveal/results |
| Historical normal/free/friend/limited | Browsable; disabled pending complete pool/master data and validation |
| Tickets / important-item costs | Requirements and stored counts projected when tables exist; purchases disabled |
| Step-ups | Current stored step/lap and current cost/guarantees visible; purchases disabled |
| Boxes / selection / mixed rewards | Metadata and unavailable reason; separate transaction and reward adapters still required |
| Historical rates | Existing definition weights/notices, not invented original server probabilities |

No additional unit metadata, summon rates, guarantees, currency grants, save schema or animation coverage was changed. Idle 417, attack 414 and production attack-to-idle pairs 413 remain the Phase 6 coverage. Missing-animation research remains paused. The Developer Lapis tool and Phase 7A browser are preserved.

## Upstream fixes reviewed and applied

The exact pinned Phase 7A upstream comparison was reviewed; no upstream checkout was merged.

| Correction | Treatment |
|---|---|
| Explicit tier unit rarity | Minimal `PlayerState.expand_pool` correction uses each explicit unit's master rarity when the tier has no featured branch, matching the reviewed upstream change |
| Step-specific pools | Minimal `roll_gacha` correction expands the current step's pool override instead of always expanding the banner pool |
| Stale/unknown offer rejection | Native facade accepts only the known primary/secondary IDs and validates before roll; original-client handler left untouched |
| Rollback | Reuses existing iOS `SummonService` full-state/dirty rollback, including save failure; no wholesale upstream `PlayerState` replacement |
| NV Guaranteed EX Summon B | Corrected in the detached iOS definition projection to item 1209001902 ×10; offer remains disabled. Shared named JSON unchanged |
| Ticket-group rates display | Native ticket-only requirement label avoids Free; legacy HTML renderer is not used by this menu and was left unchanged |

The two shared engine corrections have isolated regressions. They do not change the two demo banners' tier definitions, prices or guarantees. iOS strict malformed-campaign refusal remains in `offline_entry.initialize`. Broader Android, party, battle, trust, inventory and upstream save-quarantine changes were not imported.

## Rebuild and test

Run from the repository root. Use a Python installation with Pillow for import tools (the system `python3` used here has Pillow; the existing runtime-preparation `.venv` does not).

```sh
python3 source/ios/content_tools/recover_menu_art.py
python3 source/ios/content_tools/import_menu_art.py
python3 source/ios/content_tools/import_global_menu.py
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj -scheme FFBERevival -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath /private/tmp/FFBERevival-Phase7B-Simulator CODE_SIGNING_ALLOWED=NO build
```

`recover_menu_art.py` uses the complete committed lock on a new checkout, including the permanent expansion; no need to rerun the first-observation expansion script. Restore private Phase 6 resources and ZIP indexes first, then this tool can resume only missing pinned PNG members. It never overwrites an existing mismatched source. `import_menu_art.py` and `import_global_menu.py` produce separate versioned outputs and verify reproducibility. Native art lock pin must match `global-menu-art.lock.json`; deliberate changes require review and a new pin. Build-time packaging verifies the two new bundles and retains all previous animation/content bundles.

```sh
python3 -m unittest discover -s source/ios/tests -p test_banner_menu.py -v
python3 source/ios/tests/test_native_client.py
xcrun simctl install booted /private/tmp/FFBERevival-Phase7B-Simulator/Build/Products/Debug-iphonesimulator/FFBERevival.app
xcrun simctl launch booted com.example.ffberevival.dev --banner-menu-test
```

The explicit diagnostic launch uses a new `Application Support/FFBERevival/validation/menu-<UUID>/campaign` root. It does not instantiate the normal campaign backend. Normal launch opens the regular app. Optional capture flags: `--menu-standard`, `--menu-limited`, `--menu-banner 49`, `--menu-banner 1`, or `--menu-page single-confirm` / `eleven-confirm` (the latter two are non-purchasing confirmation display captures).

Signed physical build with the existing ignored `Signing.local.xcconfig`:

```sh
xcodebuild -project source/ios/native/FFBERevival.xcodeproj -scheme FFBERevival -configuration Debug -sdk iphoneos -destination 'generic/platform=iOS' -derivedDataPath /private/tmp/FFBERevival-Phase7B-Device build
codesign --verify --deep --strict /private/tmp/FFBERevival-Phase7B-Device/Build/Products/Debug-iphoneos/FFBERevival.app
xcrun devicectl device install app --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 /private/tmp/FFBERevival-Phase7B-Device/Build/Products/Debug-iphoneos/FFBERevival.app
xcrun devicectl device process launch --device 6CC25DBF-80E7-570F-88FC-DEC6DB94EF34 --terminate-existing com.example.ffberevival.dev --banner-menu-test
```

Keep the original bundle identifier and signing team. Install in place; never uninstall or restore the normal campaign for testing.

## Validation

136 tests pass across 19 isolated suites: existing summon/save/network guard/assets/crystal/OBTAINED/cold-recovery regressions plus ten new menu tests and the narrowed committed-reveal helper preservation check. Legacy test harnesses were updated for the new authorized menu API, while immutable animation locks and reveal-state checks remain. The additional Swift URLSession contract verifies live menu and quote JSON against a temporary real HTTP campaign. Final test/build evidence accompanies this report.

New checks cover zero state/dirty/save mutation, repeated read-only navigation, two exact playable IDs, live 500/5000 prices, current balances, insufficient funds, usage caps, unsupported and stale-offer rejection before roll, ticket counts and step/lap reads, B-ticket correction, explicit-rarity and step-pool corrections, rollback on save failure, art identity/corruption/reproducibility and native geometry at 320/375/390/393/402/440/768-point content widths. Sprite/animation locks remain unchanged.

Simulator checks: actual UI cancellation left 10,000 test Lapis; an eleven purchase committed once, entered the existing tap-to-break crystal, showed OBTAINED and Skip All returned all eleven actual awards at 5,000 Lapis. Returning to banners did not purchase again. Screenshots include Rare, Standard, Limited, exact-ID details, unavailable historical banner, both confirmations and eleven results. The purple ribbon identifies isolated accounts, not production artwork. Screenshots are visual evidence, not an assertion that every historical banner is executable.

Physical iPhone 16 Pro: signed arm64 build and signature verification passed. Install commands timed out waiting for Mac acknowledgment, but subsequent launch and the new on-device diagnostic report confirmed the update was installed and executing. The report records 471 entries, unchanged state and identical save bytes across menu access. This is actual device execution evidence, distinct from merely compiling for arm64.

The user explicitly approved private campaign exports to `/private/tmp` solely for before/after comparison. Normal campaign SHA-256 before and after the update is identical:

`386f167b5233b3a0707226a1f88ccd022394039060d4319ae76d81a7b985f09a`

No normal-campaign Lapis or tickets were spent. Save contents are not included in this report or Git. `Campaign-Integrity.json` stores only hashes and comparison results. Hands-on physical screen/transaction/Airplane Mode results are recorded separately when confirmed; the on-device automated report alone does not prove those visual/manual checks.

## Phase 7C recommendation

First review this original-style menu and close the font/header/spacing authenticity gaps using actual Global footage. Keep the secondary archive convention separate from original tabs. Recover further exact English artwork in small locked batches rather than copying the whole dataset.

Then extend complete master/name/rarity and item/ticket metadata, validate full pools and effective guarantees, and introduce native ticket DTO/selection with stale quote handling and transaction-failure tests. Enable a small ordinary-banner subset only after isolated end-to-end validation. Step-ups need full per-step/lap and bonus-reward validation; boxes/selection/mixed rewards require distinct request/result adapters. Keep the existing committed crystal/OBTAINED component and saved results fallback. Do not resume missing-animation research or expand production offers as a side effect of menu browsing.

## Final physical-device user check

The user confirmed that the purple isolated menu test works correctly: category browsing, displayed prices, cancellation, single summon, crystal/OBTAINED presentation and return to results/menu. The user chose to skip Airplane Mode testing for Phase 7B; it is **not claimed as passed**. Backend network guards, local asset packaging and existing automated offline tests passed, but they do not replace that manual device check.

Current final build sizes (uncompressed app bundles): Simulator 146,759,578 bytes; signed arm64 device 126,294,257 bytes. Both include all 46 selected banner PNGs, 24 menu UI PNGs and embedded Python. Source assets remain private/ignored.

Final post-manual-test normal campaign checksum also matches the baseline exactly; `Campaign-Integrity.json` records the third comparison. No normal campaign purchase occurred.

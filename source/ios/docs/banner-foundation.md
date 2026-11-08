# Phase 7A — banner foundation and research

## Scope and safety

Phase 6D-4C/4D checkpoint: `6da00ff0f2700428b7950c8dae3fd5140fcbf7c3` (`feat(ios): expand original unit attacks and obtained animations`). This commit precedes the Phase 7A research changes. Phase 7A remains uncommitted for review. Nothing was pushed or merged. Production summons, campaign storage, rates, crystals, attack/idle presentation and Developer Lapis tool remain unchanged. No iPhone installation or campaign access was needed for this research.

The new Developer → Browse read-only banner catalog uses a bundled immutable snapshot, not a live player. It cannot purchase anything. It is a native research browser with documented provenance, not the finished original Global menu. Search, archive-group filtering, original-client tab filtering, details, missing-art placeholders and declared offer text are available. No new production banners are enabled.

## Rebuild the optional research content

Run from the repository root, using the existing development Python environment with Pillow:

```sh
source/ios/.venv/bin/python source/ios/content_tools/audit_summon_ui.py
source/ios/.venv/bin/python source/ios/content_tools/recover_banner_research.py
source/ios/.venv/bin/python source/ios/content_tools/import_banner_research.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj -scheme FFBERevival -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath /private/tmp/FFBERevival-Phase7A-Simulator CODE_SIGNING_ALLOWED=NO build
```

If the project generator is not needed, retain the checked-in Xcode project; see the native README for the established generation command. The source snapshot and private resource backups are both necessary: Git intentionally contains no copyrighted artwork or Python runtime binary. Restore the earlier complete Pre-6D-4C backup and then the verified Post-6D-4D incremental overlay using its `restore_resources.py` instructions. That restore was tested with a fresh Simulator build. The overlay depends on the original base backup; retain both.

New research dependencies are ignored `.local/phase7a/sources`, versioned `BannerResearch` output, and cached `.local/phase6a/source-indexes/data-001-index.json` / `data-010-index.json`. Preserve `.local/phase7a` privately if retaining this exact research snapshot. The two small JSON locks are source-controlled provenance/checksum metadata, not game assets. The art recovery tool checks pinned ZIP-index identities, exact member paths, CRC32, SHA-256, PNG integrity and dimensions. It requests bounded ranges with rate limiting; it does not download whole archives. Cached replay performs zero network requests. A missing optional research bundle does not disable production summons; a present but corrupt or stale bundle fails verification rather than silently shipping incorrect prices.

The bundle contains 745 compact definitions and six PNGs (four exact banner IDs), about 1.10 MB. The full 11.23 MB audit stays local and is not bundled. Regeneration fails if locked definition fingerprints or content identities change; review such changes before deliberately updating locks and the Swift expected-lock pin. Runtime loading is local and checksum-validated; no runtime download exists.

Simulator entry points:

```sh
xcrun simctl launch booted com.example.ffberevival.dev --banner-research-preview
xcrun simctl launch booted com.example.ffberevival.dev --banner-research-preview --banner-research-detail
```

The second opens the exact-ID Rhus research detail for repeatable screenshots, without opening a player or summoning. Normal entry uses the unchanged production screen.

## Catalog and backend findings

The five JSON sources contain 749 raw definitions: authored 9, catalogue 273, community 369, named 90 and standard 8. The active merged result is 745: two standard definitions disabled and two raw duplicate IDs overridden by source precedence. The archive browser exposes 469 distinct entries; 276 are hidden aliases or deduplicated offers. These are definitions and browsing entries, not a claim that 745 banners are currently playable on the 423-unit iOS dataset.

Families: 705 normal, 18 limited, 13 step-up, six free, one friend, one selection, one box. Declared options include 708 records with a single draw, 704 with a multi draw, and 650 with a ticket-group reference. These counts overlap. The inventory retains full declared costs, guarantee slots, featured IDs, schedule/caps, source fingerprints and missing dependencies. Tier weights are definitions, not recomputed guaranteed-slot probabilities or proof of original Global server rates.

The archive's Season 1–4 / Collaborations groups are a revival navigation convention, distinct from original-client Rare / Standard / Limited tabs. Archive-adjusted wire types yield 38 Standard, 17 Rare and 690 Limited records in this snapshot. The groups share eight permanent entries: exclusive counts are Standard 1, Season 1 68, Season 2 140, Season 3 103, Season 4 128 and Collaborations 21. Do not infer original Global tab behavior or historical availability from season labels.

Current iOS production exposes only authored IDs `9100203` (Charlotte/Friese/Shepard) and `49` (Summer Fina & Lid / Summer Folka & Citra), each 500 Lapis single / 5,000 Lapis eleven. Structural facade checks accept 692 catalog records but do not validate their pools against current metadata. Tickets, step-ups, boxes, selection and mixed rewards require additional adapters/data and tests before rollout.

| Capability | Actual implementation | iOS gap / limitation |
|---|---|---|
| Unit draws, costs, guarantees, currency, inventory | `PlayerState.roll_gacha`, wrapped by transactional `SummonService` | Keep existing path; validate expanded master coverage |
| Group/named tickets and rarity floors | Python engine and original-client request handlers | Expose ticket inventory, eligible ticket IDs and explicit selected offer; native API currently has no ticket parameter |
| Step/lap progress, rewards, caps | Python engine | Native model missing; local step-specific pool issue must be fixed before affected banners |
| Box stock / advance | `gacha_box` | Separate handler; do not pretend it is a normal draw |
| Unit/prism selection | `exvius_gacha_select` | Needs full master/item tables and dedicated selection request |
| Free/friend/item/important-item costs | Definition and engine paths | Current UI only presents demo Lapis; item tables/inventory are not in native state DTO |
| Rates HTML | `gacha_rates.page` | Offline native details should preserve notices and effective guarantee semantics |
| Persistent history | Last pull/result and usage counters | No full transaction-history API; do not fabricate one |
| Historical schedules | Fields and served dates | General historical availability is not consistently enforced by `roll_gacha`; account caps are real checks |

Reuse actual Python behavior rather than converting these rules to Swift. The catalogue helper creates a separate temporary data root in a fresh subprocess, forbids `PlayerState` construction, save and roll, and verifies no player/files were created. Its detached projection cannot mutate definitions. Never call `gacha_archive.menu(player, selection)` for a read-only view: it deliberately changes archive preference and dirty state.

Android's `LocalGameBridge.summonArchive` calls `android_game.summon_archive`, which uses `ffbe_gacha.all_banners` / `gacha_archive.menu` under a state lock and saves explicit selection. The original-client gacha-info handler builds master rows; purchase requests carry banner/detail/repeat/ticket identifiers. The web rates route delegates to `gacha_rates.page`; it is not another random engine. Keep original protocol obfuscation in Python and expose clear typed DTOs to Swift.

## Original UI and provenance

Global 9.1.0 has 39 recovered summon layout CSVs. Their decoded bytes match the corresponding English-patched Memorial 11.1.0 layouts; Memorial adds three AdGachaList layouts. Matching layouts do not prove identical behavior. The comparison tool records exact decoded hashes and all layout rows.

| Element | Evidence / availability | Treatment |
|---|---|---|
| Top list / tabs / scrolling | Original Global `layout_gachaTop_640x1136.csv`, gachaTab and related variants | Authoritative future anchors; research preview uses native controls |
| Main / secondary / ticket / step button layouts | Recovered gachaButton, ticket, step and related CSVs/atlas frames | Reuse pinned original or verified preservation frames in production work |
| Confirmation, details, result, box | Original Global layouts, including banner/detail regions | Layout evidence available; account-specific strings and behavior still Python/native work |
| Lapis / price / numeric decoration | Existing Phase 6B recovered atlas/font resources | Existing production components unchanged |
| Rates and insufficient-currency text | Backend rates and transaction errors; layout evidence | No claim to complete original localized string/UI recovery |
| General original font | No complete verified font mapping established here | Native research system font is an explicit adaptation |
| Banner illustrations | 533 matching indexed paths, including 104 native English main/sub paths | Index presence alone is not image verification |

Global-targeted preservation gacha atlases have 53 / 74 / 16 frames; Memorial has 42 / 70 / 20. Across shared frame names, 122 of 126 normalized source-canvas RGBA images match (38/40, 68/70, 16/16). Rotation, trimming and source dimensions are respected by the existing TexturePacker decoder. Four differing shared frames and all version-only names are enumerated in `UI-Comparison.json`. No Memorial image is imported into the new browser.

Recovered sample: six images, 395,474 transferred bytes, exact-ID lookup. IDs 9200001 and 9200023 have English native main/detail PNGs from Global-targeted preservation data-010. IDs 9100203 and 49 use separately labeled community-calendar images from data-001. Global-targeted preservation is not proof of byte-for-byte original retail Global CDN origin. The four sample IDs include hidden/deduplicated demo definitions, so the default archive-visible filtered list shows two illustrated records. The full inventory retains all four image mappings. No image is substituted by character name.

The reference 640-wide Global layout has list origin y338, banner 640×160, text y483, tabs near y250 and header near y172. For later reconstruction, scale x and widths by available safe-area width/640; translate recovered content origin relative to a separately fitted header, then fit scrolling content height. A 640×1136 scene is not a modern SwiftUI safe-area rectangle: account for top/bottom insets and original clipping/anchor hierarchy. The current native browser does not claim to reproduce these coordinates.

## Upstream compatibility

Local comparison base is `4d35ad5879ed1658db8c5c48b6928ed27d649d1b`; upstream HEAD is `621b386e007240598314b83682a501ed2f128d10`. Upstream is three commits ahead of the shared base, local seven commits ahead after checkpoint. Comparison used an isolated bare audit repository; no fork refs or working code were updated.

Useful changes in upstream v0.1.24/v0.1.25:

- Correct actual rarity for explicit tier unit lists.
- Honor a step's own pool. Local code expands the banner pool instead, affecting step 2 of IDs 801060, 801070, 801080, 9100125, 9100126 and 9100127.
- Reject stale/unknown offer details before charging; broaden original-client transaction rollback.
- Correct NV Guaranteed EX Summon B (`9200023`) from important item 110260 ×10 to item 1209001902 ×10, retain its archive/filter visibility, and fix ticket-group rates cost display.
- Additional trust, equipment, party, mail, battle and Android changes are outside this iOS banner phase.

No authored/catalogue/community/standard rate JSON changed in the examined range; execution fixes can still change actual outcomes. The one named-banner cost correction must not be confused with unchanged pricing. Do not merge the full upstream `PlayerState` blindly: upstream save-error quarantine/fresh-load behavior intersects with iOS's stricter refusal to reset damaged campaigns, and existing iOS rollback already covers persistence failures. Review targeted fixes with isolated step/ticket/rollback regressions before enabling affected offers in Phase 7B. Wider upstream integration belongs to a separate reviewed change.

Primary evidence: [upstream comparison](https://github.com/Elvlin/exvius-offline/compare/4d35ad5879ed1658db8c5c48b6928ed27d649d1b...621b386e007240598314b83682a501ed2f128d10), [pinned gacha handler](https://github.com/Elvlin/exvius-offline/blob/621b386e007240598314b83682a501ed2f128d10/source/server/ffbe_gacha.py), [pinned player engine](https://github.com/Elvlin/exvius-offline/blob/621b386e007240598314b83682a501ed2f128d10/source/server/player_state.py).

## Phase 7B architecture and sequence

1. Review the targeted upstream fixes in isolation. Add step-pool, explicit-rarity, stale-detail, B-ticket, guarantee and persistence-failure tests before activating these features. Keep Android changes separate.
2. Build a Python read-only catalogue/quote API with explicit `banner_id`, `offer_id`, currency/ticket requirements, effective draws/guarantees, step/lap state, eligibility reasons, featured IDs, rate notices and source provenance. Quotes must inspect copies and never create `banner_state` or save archive preferences. Distinguish definition availability from account eligibility. Return only supported/validated offers; retain others as labeled unavailable research records.
3. Keep `SummonBackend` embedded-first and HTTP-compatible. Add typed Swift DTOs for catalogue, quote, ticket balances and committed receipts, keeping group and Global-tab filters separate. Swift stores navigation locally, not in campaign schema. Python computes all prices, caps, rates and rewards.
4. Recover exact English banner art in small checksum-locked batches. Fill missing UI dependencies from verified Global layouts/frames; show explicit placeholders otherwise. Keep Memorial candidates separate until individually validated. Resolve original text/font gaps explicitly.
5. Implement the original-style native list/details/confirmation around recovered anchors, safe areas and multiple device sizes. Do not show static research costs as live quotes. Revalidate selected detail/ticket/current step at commit. Preserve rollback; define retry/idempotency behavior before introducing transaction retries.
6. After one backend commit, pass the actual committed awarded IDs/rarities to the existing crystal → OBTAINED → results flow. Never purchase again on reveal, background/resume, retry or skip. Preserve results fallback. Mixed reward types, boxes and selection need distinct DTOs/screens, not invented unit rewards.
7. Enable existing two banners first, then validated ordinary banners, then ticket/free/friend families, then step-ups, finally boxes/selection after dedicated coverage. Expand full master metadata and inventory dependencies before pools outside 423 target IDs. Test isolated campaigns only, offline, low currency, cancellation, repeated input and relaunch.

The animation recovery scope is unchanged: 417 idle, 414 attacks, 413 production attack-to-idle target pairs across 423 target IDs. Missing animation research remains paused. No save migration is proposed in Phase 7A.

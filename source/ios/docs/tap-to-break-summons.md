# Phase 6C-4 — committed summon → tap-to-break → saved results

Production summons now insert the shared original-asset crystal renderer after a
correlated successful backend response. **The production crystal never opens on a
timer.** It arrives, waits for a tap indefinitely, opens once, then reveals the
actual committed awards. Skip and unavailable/interrupted playback use the same
saved-award result boundary. The Developer automatic animation demo remains intact.
This remains reconstructed presentation, not recovered BISHAMON playback.

## Preservation

Work stayed on `ios-port`. Phase 6A–6C-3 uncommitted source, locks, assets and reports
were retained, including the prior app/project/packaging edits and two untracked
`.DS_Store` files. No reset, restore, uninstall, bundle-ID change, full backup,
upstream operation or asset commit occurred. Python reward logic and Android
implementation were not modified. The 423-unit artwork library and existing UI
resources are reused. No new asset downloads were necessary.

## Actual transaction and recovery path

`GlobalSummonScreen` shows the existing `SummonConfirmation` sheet. Its injected
async callback reaches `ContentView.summon`, then `SummonModel.summon`, then the
selected `SummonBackend` (embedded Python by default, HTTP development mode still
available). The Python service calls the existing `PlayerState.roll_gacha()` once,
then successfully saves before returning the result/state envelope.

The backend already persists `gacha.last_pull`, including the complete ordered
awards, banner ID and draw count. `offline_entry.state()` exposes that saved pull;
`SummonModel.refresh()` restores it. Consequently a second persistent award journal
was unnecessary and would introduce another authority to reconcile.

After success, the frontend creates an immutable `CommittedSummon` receipt only if:

- result banner/count match the requested banner/offer;
- result awards match the returned state's saved `last_pull` in original order,
  using instance ID, exact master ID and granted rarity;
- award IDs are nonempty/unique, newly introduced relative to the pre-request roster,
  and present with their exact master IDs in the returned inventory;
- the backend identity has not changed during the request.

Names are intentionally excluded from correlation because the service can enrich
names after saving. UUIDs identify frontend presentations only; they are not backend
transaction IDs. Unsupported future response shapes fail correlation and require
saved-state refresh rather than guessing, rerolling or discarding backend progress.

The screen freezes the verified awards and queues presentation until the confirmation
sheet finishes dismissing. It does not immediately set `showResults`. Background
refresh cannot replace the frozen list. Opening completion or a safe fallback sets
results from that receipt, preserving the existing single/11-unit results grid.
The parent also ignores any alternative award selection from a completion callback.

The original busy/connected-identity guard and confirmation request guard remain.
Neither animation nor recovery can access a `SummonBackend`. Failed, ambiguous or
uncorrelated responses create no crystal receipt and leave `needsRefresh` set;
there is no automatic POST retry. Refresh reconciles the persisted last pull.

## Explicit production state machine

`TapSummonClock` is a Foundation-only state machine, separate from the Developer
clock but sharing its pose/material/scene implementation:

| State | Transition | Behavior |
| --- | --- | --- |
| arriving | 0.90 authored source seconds → waitingForTap | Arrival taps are ignored, never buffered |
| waitingForTap | First valid active tap only → opening | Bounded idle loop, no deadline or automatic transition |
| opening | 1.20 authored source seconds → revealing | Repeated taps are ignored immediately |
| revealing | 0.40 authored source seconds → finished | Clean transition to the actual saved result |
| finished | No further advance/tap completion | Renderer display link stops; completion occurs once |

Idle opening progression stays fixed at 0.90 seconds, while an independent active
motion clock advances floating, texture drift and particles continuously. It does
not reset at the idle loop boundary. This corrects the small periodic stutter noticed
during physical testing. Opening progression stays below its boundary even after
arbitrarily long waits. No animation duration, background transition, view refresh or resume can
substitute for a tap. These are authored reconstruction seconds, not decoded BMB
keys. Scheduling gaps retain the existing renderer's 100 ms per-tick cap.

The presentation area (including its prompt/spacers) accepts taps, with a separate
Skip button. It displays “Tap to Break” only when ready for input. It is accessible
as a button and supports an accessibility activation action. Swipe dismissal is
disabled, and full-screen cover dismissal still has a safe result fallback.

On inactive/background, the shared controller pauses its clock/display link while
preserving the production phase. On active return it resumes the same phase with
no elapsed background time. Waiting remains waiting; opening resumes without a
second trigger. Developer controls keep their existing explicit Play behavior.

`SummonRevealGate` is the shared idempotent completion boundary with explicit opened,
skipped, unavailable and interrupted reasons. It returns the original receipt's
awards once. The production component accepts separate completion/fallback actions;
both route to the saved-result screen. It clears renderer callbacks and stops the
scene before dismissal. Missing/corrupt resources safely bypass presentation.

## Rarity mapping

This is a reconstruction mapping from **granted rarity only**:

| Granted rarity | Visual |
| --- | --- |
| 1–3 | Blue |
| 4 | Gold |
| 5–8, including NV/NV+ metadata | Rainbow |
| Missing, malformed or unsupported | Blue if no valid rarity is available |

An 11-pull uses the highest supported awarded rarity for **one** crystal, then the
existing 11-character grid. Unknown entries are ignored when other valid rarities
exist. No artwork, name or sprite color participates. Malformed visual rarity
metadata decodes to nil rather than causing a committed reward to be retried; the
original backend save and awarded unit identity are not rewritten.

## Cold relaunch and escape paths

Force-close destroys the in-memory crystal state. On cold launch the normal app
only refreshes state; it never calls summon automatically. Use **View latest saved
summon** on the banner screen, or the Developer saved-summon list, to view the exact
persisted awards. Recovery deliberately shows results directly rather than resuming
an uncertain animation stage. A new summon replaces last_pull, as before.

The latest-result button also serves as an escape if a presentation request cannot
be displayed. It remains available with committed pending results. Navigating away
or losing the view cannot remove backend rewards. A device/driver crash is recovered
through the persisted last pull on relaunch; it is not claimed to be catchable as a
normal SceneKit error. Skip remains available if a renderer appears unusable.

## Tests and reproducibility

New tests are in `tests/test_tap_summon.py`, with two Swift smoke programs. They test:
arrival taps, simulated indefinite waits, one opening, repeated taps, waiting/opening
pause, single completion, typed Skip/failure/interruption idempotence, one single and
one 11-pull, duplicate-confirmation blocking, refusal, malformed/unsupported rarity,
correlation rejection, no automatic retry, exact reconciliation after a post-commit
error, and fresh-process recovery without charge or save write.

The HTTP fault test uses the real Python engine and counts `roll_gacha` calls. It
injects an HTTP 500 **after** the third durable commit. The frontend reports failure,
does not reroll, then refreshes the committed result. This is a controlled response
failure, not a claim that an actual TCP-loss race was exercised.

```sh
cd ~/Documents/Projects/exvius-offline
source/ios/.venv/bin/python -B source/ios/tests/test_tap_summon.py
```

The full regression set still runs each file separately with its documented
interpreter; loopback HTTP tests need a permitted local test-server socket. Asset
import/reconstruction tests use system Python/Pillow; backend tests use `.venv`.
There are 68 Python test methods including the three new cross-process contracts,
plus Swift checks executed by those suites/native-client harness.

```sh
python3 source/ios/native/generate_project.py
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6C4-Simulator \
  CODE_SIGNING_ALLOWED=NO build
xcodebuild -project source/ios/native/FFBERevival.xcodeproj \
  -scheme FFBERevival -sdk iphoneos -destination 'generic/platform=iOS' \
  -configuration Debug -derivedDataPath /private/tmp/FFBERevival-Phase6C4-Device build
```

Existing local runtime, original unit/UI and crystal reconstruction bundles remain
prerequisites. Keep the existing signing team and `com.example.ffberevival.dev`.
Install as an update, never uninstall. No changes to the asset pipeline are needed.

## Isolated device diagnostics

Launch-only routes bypass `ContentView` and the normal campaign:

- `--tap-summon-diagnostics`: new UUID test campaign, real embedded single/multi,
  duplicate/refusal checks, shared renderer held past the old automatic opening
  deadline, tap/repeat/interruption/fallback checks, captures and a recovery marker.
- `--tap-summon-reload-check`: a separate cold process loads that exact test campaign,
  verifies saved IDs/balance, and asserts zero summon requests. Never resets it.
- `--tap-summon-lab`: fresh 10,000-Lapis **test-only** campaign with the actual
  production banner/confirmation/crystal/result components and purple isolation label.
  Use this for physical button, tap and Skip confirmation.

Diagnostics write only under Application Support `FFBERevival/validation/tap-summon`.
The counter wrapper counts requests and successful responses; an insufficient-funds
request is not a successful commit. Automatic renderer tests and pure completion
checks are distinct from real SwiftUI touch/Skip tests and manual Home/radio tests.

A normal cold launch does not retain diagnostic arguments. Do not test summons in
the normal campaign after closing a lab; relaunch the explicit lab route instead.
The old Developer gray inspector and Blue/Gold/Rainbow controls remain available.

## Phase 6D recommendations and limits

First review the actual production cover on device, including indefinite waits,
Skip and Home/resume. Then polish idle-loop continuity, “Tap to Break” typography,
opening surfaces, HDR/bloom and transition pacing. Preserve the authoritative saved
award boundary. The current fracture groups remain reconstructed open surface
clusters, not original shard meshes. Appearance mappings and the one-crystal 11-pull
are explicitly reconstruction choices. Full BISHAMON recovery is not claimed.

Long thermal/Instruments runs, actual transport-loss stress and force-termination
*during* an in-progress filesystem commit remain outside the short test scope.
The backend's existing rollback/atomic-save protections remain unchanged. No normal
campaign test summon is required to verify any of these presentation behaviors.

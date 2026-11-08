# iOS development

This directory contains backend verification, a summoning facade, a development HTTP
API, and a native SwiftUI summon app with bundled Python. It is not a completed port. The existing Android
implementation and Python gameplay logic are unchanged.

For the current summon interface, follow [the Phase 6B interface guide](docs/summon-interface.md).

For the 423-sprite offline library, follow [the Phase 5C artwork-library guide](docs/artwork-library.md). The [Phase 5B guide](docs/unit-content.md) records the original metadata and three-image prototype.
It imports the pinned small Global-targeted sample into ignored local build resources.
The native screens have real names for all 423 demo IDs and exact-ID sprites for
Ludmille, Rain and Lasswell. Other forms use a labeled missing-art placeholder.

Start with [the offline backend guide](docs/offline-backend.md) for runtime setup,
architecture, builds and iPhone checks. The [HTTP development guide](docs/native-prototype.md)
remains available for Phase 3 debugging.

## Layout

- `docs/architecture.md`: backend boundaries, proposed hosting, and feasibility gates.
- `docs/compatibility.md`: Android components and their proposed iOS replacements.
- `tests/smoke_backend.py`: real in-process backend verification using temporary,
  synthetic resources and a tiny authored response; no proprietary game data.
- `requirements-smoke.txt`: desktop test dependencies, not iOS frameworks.
- `.gitignore`: local environments and generated iOS build artifacts.

The standalone summoning prototype is documented in [docs/summoning.md](docs/summoning.md).
Run `prototype/summon_cli.py --demo` using the environment below for the terminal UI.
It calls the existing summon backend; it does not depend on Memorial's summon UI.
`prototype/summon_service.py` is the platform-independent facade and
`prototype/demo_data.py` supplies explicit placeholder metadata when real tables
are absent. `tests/test_summon_service.py` verifies transactions and persistence.

The Xcode project and embedded bridge are in `native/`; `embedded/` contains the
JSON boundary to the existing service. Runtime downloads stay under ignored `.local/`. Do not store IPAs, extracted clients, game assets,
signing identities, or executable dependencies in this source directory. Keep personal
inputs outside the repository; `.local/` is ignored for optional local experiments.

## Desktop smoke test

Python 3.10+ is required. From the repository root on Windows:

```powershell
python -m venv source/ios/.venv
source/ios/.venv/Scripts/python.exe -m pip install -r source/ios/requirements-smoke.txt
source/ios/.venv/Scripts/python.exe -B source/ios/tests/smoke_backend.py
```

On macOS/Linux, replace `Scripts/python.exe` with `bin/python`.
Run the script as its own process; it isolates backend environment settings and
installs a process-lifetime audit hook that rejects socket creation, DNS, bind,
and connect operations. No listener, Android SDK, IPA, or full data download is needed.

Exit 0 means the backend initialized, its pipeline registry validated, a local file
was served, a real encrypted request was decrypted/dispatched/re-encrypted, currency
operations behaved as expected, and a temporary save reloaded with the expected
balance. Exceptions return exit 1 with diagnostics. Temporary data is cleaned on exit.

The authored marker response verifies transport, not original game response content.
Empty master tables plus authored starter-unit/equipment identities exercise
minimal engine initialization; this
does not establish content completeness, playable battles, summon correctness,
fresh-process campaign restart, or iOS compatibility. No gameplay methods are mocked.

Fixtures are created below the ignored `source/ios/.local/` directory and removed
after each run. Keeping them on the checkout's drive avoids existing Windows
cross-drive diagnostic-path limitations. Personal saves are never opened.


The Developer tab also includes [the isolated original crystal-mesh diagnostic](docs/crystal-recovery.md). Original crystal animation playback is not yet recovered.

Phase 6C-2 adds [bounded BMB structure and version analysis](docs/crystal-bmb-analysis.md). Original animation playback remains disabled.

Phase 6C-3 adds [the isolated original-asset crystal reconstruction](docs/crystal-reconstruction.md), with Blue/Gold/Rainbow layers and authored arrival/opening motion. Production summons remain unchanged.

Phase 6C-4 integrates [tap-to-break after a verified committed summon](docs/tap-to-break-summons.md), with indefinite idle, Skip/fallback and existing saved-result recovery.

Phase 6D-1 adds an isolated [character reveal research gallery](docs/character-reveal-recovery.md). Production summons/results are unchanged; the remembered pedestal remains unconfirmed.

Phase 6D-2 inserts [animated committed-award character reveals](docs/animated-character-reveal.md) after crystal opening. Validated on Simulator only; physical-device work awaits explicit approval.

Phase 6D-3A: [falling crystal entrance and TOUCH SCREEN](docs/falling-crystal-entrance.md), including isolated device validation and rebuild commands.

Phase 6D-4: [original unit animations and personal Lapis control](docs/unit-animations.md).

Phase 6D-4B: [expanded animation recovery and searchable gallery](docs/unit-animation-expansion.md).

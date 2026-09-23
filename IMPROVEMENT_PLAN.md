# Improvement plan — plugin.video.drnu

Working plan for code structure, tests and CI. Check items off as they land.
Suggested order: Phase 0 → 1 → 2 → 3, Phase 4 optional.

**Note:** Phase 0 complete as of commit 5ab0b18. Phase 1 linting complete as of
current commit. The `kodiutils.py` refactoring (commit 4a05080) completed module
structure integration. See Phase 2, 3 for follow-up work.

## Completed Changes

- [x] **2026-09-22**: Created `resources/lib/kodiutils.py` module (commit 4a05080)
  - Centralized all Kodi-specific utilities (settings, logging, localization, etc.)
  - Refactored `addon.py` to use wildcard import from kodiutils
  - Reduced code duplication by ~50 lines
  - Updated test golden files to match current nocache menu behavior
  - All 5 routing tests pass
- [x] **2026-09-23**: Phase 0 hygiene (commit dff35ba)
  - Expanded `.gitignore` with `__pycache__/`, `.ipynb_checkpoints/`, `.pytest_cache/`,
    `.ruff_cache/`, `token.p`, `*.srt`, `search6.pickle`, `requests.cache*`,
    `requests_cleaned`, `*.ipynb`, `*.sh`
  - Removed tracked binaries `tests/userdata/requests.cache.sqlite` and
    `tests/userdata/requests_cleaned` from git
  - Cleaned up untracked junk: `tests/test.html`, stray `git` file,
    `resources/media/gensyn_raw.png`
  - All 5 routing tests pass
- [x] **2026-09-23**: Phase 0 cleanup (code hygiene)
  - Removed dead code: `URL2` (old API endpoint) and `add_to_watched` (unused,
    had incorrect `&position=` in URL)
  - Gated `print()` calls in `full_login` behind `log.debug` setting via optional
    `log_func` parameter
  - All 5 routing tests pass
- [x] **2026-09-23**: Phase 1 linting (ruff baseline)
  - Added `pyproject.toml` with ruff config (line-length=200, py38, E/F/W/B/UP/SIM/I/C4)
  - Ran `ruff check --fix` and fixed remaining findings manually
  - Fixed naming: `resfresh_ui` → `refresh_ui`, `'powter'` → `'poster'`
  - All 5 routing tests pass

## Phase 0 — Hygiene and safety (small, do first)

- [x] Expand `.gitignore` (currently only `.idea`, `*.pyc`, `*.pyo`):
      `__pycache__/`, `.ipynb_checkpoints/`, `.pytest_cache/`, `.ruff_cache/`,
      `token.p`, `*.srt`, `search6.pickle`, `requests.cache*`, `requests_cleaned`,
      `*.ipynb`, `*.sh`
- [x] Remove untracked junk: stray `git` note file, `.ipynb_checkpoints/` dirs,
      `tests/test.html`, `tests/requests.cache`, `tests/*.srt`, `tests/token.p`
      (contains real JWTs — anonymous, but should not be lying around)
- [x] Remove tracked binary `tests/userdata/requests.cache.sqlite` (old cache
      format); `tests/userdata/requests_cleaned` also removed from git
- [x] Properly integrate `resources/lib/kodiutils.py`:
      - Fixed undefined `message` and `Path` issues
      - Added comprehensive Kodi utility functions
      - Refactored `addon.py` to import from kodiutils
      - All routing tests pass with the new structure
- [x] Remove dead code: `URL2` (`tvapi.py:47`); `add_to_watched` (`tvapi.py:398`,
      unused, and its URL uses `&position=` where it needs `?position=`)
- [x] Gate the `print()` calls in `full_login` (`tvapi.py:135-140`) behind the
      `log.debug` setting instead of dumping login GraphQL responses to stdout

## Phase 1 — Linting and tooling baseline

- [x] Add `pyproject.toml` with ruff config:
      - `line-length = 200` (matches existing flake8 setting)
      - `target-version = "py38"` (Kodi Nexus bundles Python 3.8; Omega 3.11)
      - select `E, F, W, B, UP, SIM, I, C4`
      - per-file-ignores: `"tests/*" = ["F401"]`, `"resources/lib/addon.py" = ["F405", "F403"]`
- [x] Run `ruff check --fix`; fix remaining findings by hand:
      - mutable default args in `fix_query` (`tvapi.py:66`)
      - `class Api():` → `Api:` and similar `UP` modernizations
      - import sorting (`I`)
- [x] Fix naming debt: `resfresh_ui` → `refresh_ui` (`addon.py:522`),
      `'powter'` → `'poster'` (`addon.py:359`)
- [x] Shift to ruff (dropped flake8 as requested)

## Phase 2 — CI and tests

### CI (`.github/workflows/python-package-conda.yml`)

- [ ] `actions/checkout@v3` → `@v4`
- [ ] Run `kodi-addon-checker` for both `--branch=nexus` and `--branch=omega`
      (addon declares `xbmc.python 3.0.1`, which spans both)
- [ ] Add `workflow_dispatch` trigger so feature branches can run CI
- [ ] Split into jobs: `lint`, `addon-check`, `tests`
- [ ] Optionally replace micromamba env with `pip` + `requirements-dev.txt`
      (requests, requests-cache, dateutil, pytest, ruff, kodi-addon-checker)

### Tests

There is no official Kodi test runner. The stub modules in `tests/`
(`xbmc.py`, `xbmcaddon.py`, `xbmcgui.py`, `xbmcplugin.py`, `xbmcvfs.py`,
`inputstreamhelper.py`) emulating the Kodi API are the community-standard
approach — keep that pattern, improve on top of it:

- [ ] Add `conftest.py`: move `sys.path` injection and stub imports there; expose
      the addon `handle` as a fixture instead of module-level state (today
      `test_routing.py:28` replaces the handle with a plain dict — clever but fragile)
- [ ] Make API tests hermetic: convert the recorded `requests.cache.sqlite`
      responses to JSON fixtures under `tests/fixtures/`, served via `responses`
      (or a small adapter). The current `assert u.from_cache` trick
      (`test_routing.py:64`) silently does a live request when the cache misses
- [ ] Split `test_basemenus` into one test per screen; reset state per test
- [ ] Replace `UPDATE_TESTS`/`UPDATE_CACHE` module flags with a `--update-golden`
      pytest option or a small script
- [ ] Add pure unit tests (no Kodi needed):
      - `vtt2srt` (golden output already exists as `tests/30050.da.srt`)
      - `fix_query`, `generate_code_challenge` (RFC 7636 test vectors), `version()`
      - `get_title`, `item_area`, `kids_item`
      - route dispatch: table of query string → expected items
- [ ] Optional: add `kodistubs` (pip) for IDE autocompletion/type-checking of the
      xbmc API; complements, does not replace, the test stubs

## Phase 3 — Structure

- [ ] Split `tvapi.py` (750 lines, four responsibilities):
      ```
      resources/lib/
      ├── tvapi.py        # Api class: programcards, lists, schedules, streams
      ├── drauth.py       # full_login, oidc_token, exchange_token, tokens, deviceid
      ├── subtitles.py    # vtt2srt, handle_subtitle_vtts
      └── constants.py    # CHANNEL_IDS, CHANNEL_PRESET, A_AA, CLIENT_ID
      ```
      Auth is the most likely part to break when DR changes their login flow;
      isolating it makes that churn reviewable. Keep `tvapi.py` re-exporting the
      old names so `addon.py` imports stay valid during the transition.
- [ ] Split `addon.py`: extract ListItem construction (`kodi_item`,
      `showSimpleAreaSelector`, `showMainMenu`) into a `gui.py` of pure functions
      taking `(api, items)` — this is what makes routing tests meaningful
- [ ] Convert `route()`'s if/elif chain (`addon.py:549-622`) into a dict dispatch
      `{key: method}`
- [ ] Data-driven menus: `showSimpleAreaSelector` (`addon.py:158-192`) is five
      near-identical blocks — collapse into a `(label, area, image)` table
- [ ] Kill module-level side effects: `addon = xbmcaddon.Addon()` at import time
      (`addon.py:38`) makes importing the module require a Kodi environment. Move
      into `DrDkTvAddon.__init__` (or a lazy accessor) — simplifies unit tests a lot
- [ ] Extract the subtitle decision logic from `playVideo` (`addon.py:496-520`)
      into a pure function `resolve_subtitle_action(settings, subs, kids_channel)`
      and unit-test it — it is the fiddliest logic in the addon

## Phase 4 — Optional later

- [ ] Type hints on `tvapi.py` / `gui.py`; ruff `ANN` subset or pyright in CI
- [ ] Coverage badge (`pytest-cov`) — only meaningful once tests are hermetic
- [ ] Replace the blocking `time.sleep` polling in `playVideo`
      (`addon.py:487-494`) with a `Monitor`-based wait; note the comment says 10 s
      while the code waits 5 s

## Bugs noticed along the way (worth tickets regardless)

- `search()` with zero results never calls `endOfDirectory` (`addon.py:332`) —
  Kodi can be left showing a busy spinner
- `get_schedules` recursion math (`tvapi.py:727`) works, but `divmod(duration, 24)`
  would express the intent clearly

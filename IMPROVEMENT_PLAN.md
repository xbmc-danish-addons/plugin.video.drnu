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
  - Fixed all ruff findings: mutable defaults, dict() calls, blank line whitespace,
    nested if statements, ternary operators, f-strings, Python 2/3 compat code
  - Fixed naming: `resfresh_ui` → `refresh_ui`, `'powter'` → `'poster'`
  - Removed Python 2/3 compatibility code from test stubs
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
- [x] Shift to ruff (dropped flake8 as requested); CI updated to use ruff

## Phase 2 — CI and tests

### CI (`.github/workflows/python-package-conda.yml`)

- [x] `actions/checkout@v3` → `@v4`
- [x] Run `kodi-addon-checker` for both `--branch=nexus` and `--branch=omega`
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

- [x] Add `conftest.py`: move `sys.path` injection and stub imports there; expose
      the addon `handle` as a fixture instead of module-level state (today
      `test_routing.py:28` replaces the handle with a plain dict — clever but fragile)
- [x] Make API tests hermetic: convert the recorded `requests.cache.sqlite`
      responses to JSON fixtures under `tests/fixtures/`, served via a small
      adapter (`tests/fixtures_adapter.py`) that fails loudly on a cache miss.
      The old `assert u.from_cache` trick silently did a live request on miss.
      Fixture keys normalize params (sorted, `page=1` dropped, paging-context
      params stripped) so recordings under multiple spellings collapse; on
      collision the newest recording wins. Verified hermetic by banning
      `requests`/`requests_cache` during a full test run.
- [x] Split `test_basemenus` into one test per screen; reset state per test
- [x] Replace `UPDATE_TESTS`/`UPDATE_CACHE` module flags with a `--update-golden`
      pytest option (conftest.py); goldens regenerate byte-identical
- [x] Add pure unit tests (no Kodi needed):
      - `vtt2srt` (inline VTT fixture; the golden `tests/30050.da.srt` predates
        the current subtitle code and no VTT exists in the recorded cache)
      - `fix_query`, `generate_code_challenge` (RFC 7636 test vector),
        `generate_code_verifier`, `cache_path`
      - `get_title`, `item_area`, `kids_item` (called unbound with `None` self)
      - fixture-key normalization (`tests/test_fixtures_adapter.py`)
      - route dispatch: table of query string → expected items
      (`test_route_dispatch`, including the `AreaSelectorDialog` path via
      extended xbmcgui stubs)
- [ ] Optional: add `kodistubs` (pip) for IDE autocompletion/type-checking of the
      xbmc API; complements, does not replace, the test stubs

## Phase 3 — Structure

- [x] Split `tvapi.py` (750 lines, four responsibilities):
      ```
      resources/lib/
      ├── tvapi.py        # Api class: programcards, lists, schedules, streams
      ├── drauth.py       # full_login, oidc_token, exchange_token, tokens, deviceid
      ├── subtitles.py    # vtt2srt, handle_subtitle_vtts, resolve_subtitle_action
      └── constants.py    # CHANNEL_IDS, CHANNEL_PRESET, A_AA, CLIENT_ID
      ```
      Auth is the most likely part to break when DR changes their login flow;
      isolating it makes that churn reviewable. `tvapi.py` re-exports the old
      names so existing imports stay valid. `vtt2srt`/`handle_subtitle_vtts`
      are module-level functions taking their dependencies as parameters.
- [x] Split `addon.py`: ListItem construction (`kodi_item`, `showMainMenu`,
      `showSimpleAreaSelector`) moved to `gui.py` as pure functions taking
      `(plugin_url, api, menu_items, fanart_image)` — this is what makes
      routing tests meaningful
- [x] Convert `route()`'s if/elif chain into dict dispatch: an ordered
      key→handler table with one `_route_*` method per key
- [x] Data-driven menus: the simple area selector is now the `AREA_ITEMS`
      (label, area, image) table in `gui.py`
- [x] Kill module-level side effects: `xbmcaddon.Addon()` now lives behind
      `kodiutils.get_addon()` (created on first use); importing kodiutils no
      longer requires a Kodi environment. `addon.py` imports explicit names
      from kodiutils (wildcard import and its ruff ignores dropped).
      `resources_path` is a function now.
- [x] Extract the subtitle decision logic from `playVideo` into the pure
      function `resolve_subtitle_action(settings, subs, kids_channel,
      srt_subtitles)` in `subtitles.py`, unit-tested in `test_subtitles.py`.
      Behavior fix: with local subtitles enabled but no downloaded SRTs, the
      old code crashed on `[-1]`; it now falls back to the embedded stream.

## Phase 4 — Optional later

- [x] Type hints on `tvapi.py` / `gui.py` (plus `drauth.py`, `subtitles.py`);
      ruff `ANN001`+`ANN2` subset in CI. The Kodi-glue modules (`addon.py`,
      `kodiutils.py`, `tvgui.py`, `cronjob.py`, `iptvmanager.py`, `default.py`)
      are exempt via per-file-ignores — annotations there would just restate
      the xbmc API signatures. (pyright not added; ruff ANN chosen.)
- [x] Coverage badge (`pytest-cov`): `--cov` in CI, badge JSON pushed to
      `.github/coverage-badge.json` from master runs via the workflow
      `GITHUB_TOKEN`, shields.io endpoint badge in README (stale PEP8 badge
      replaced with ruff). Badge pushes are excluded via `paths-ignore` to
      avoid a CI loop. Locally: `pytest tests --cov`.
- [x] Replace the blocking `time.sleep` polling in `playVideo` with a
      `Monitor.waitForAbort`-based wait (`_wait_for_playback`), so Kodi
      shutdown interrupts it; the 10 s/5 s comment mismatch is fixed and the
      loop is unit-tested (`tests/test_playvideo_wait.py`).

## Bugs noticed along the way (worth tickets regardless)

- `search()` with zero results never calls `endOfDirectory` (`addon.py:332`) —
  Kodi can be left showing a busy spinner
- `get_schedules` recursion math (`tvapi.py:727`) works, but `divmod(duration, 24)`
  would express the intent clearly

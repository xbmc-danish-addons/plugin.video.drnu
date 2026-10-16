# AGENTS.md

Guidance for AI coding agents working on this repository.

## Project

Kodi video addon for DR (Danish Broadcasting Corporation) live and archived TV
(dr.dk/drtv). Python addon using the Kodi `xbmc`/`xbmcaddon`/`xbmcgui`/
`xbmcplugin`/`xbmcvfs` API. Runs inside Kodi (Omega), not as a standalone
program. License: GPL-2.0-only — keep headers on existing files.

## Layout

```
default.py                 entry point, calls DrDkTvAddon.route()
service.py                 background service: periodic request-cache cleanup (expire + VACUUM)
addon.xml                  addon metadata, version, dependencies
resources/lib/addon.py     routing + GUI construction (DrDkTvAddon)
resources/lib/tvapi.py     DR API client: auth, caching, listings, streams
resources/lib/tvgui.py     AreaSelectorDialog (xbmcgui.WindowDialog)
resources/lib/cronjob.py   removal of the deprecated service.cronxbmc job
resources/lib/recachescheduler.py  service-side scheduling of the re-cache crawl
resources/lib/iptvmanager.py  IPTV Manager (pvr.iptvsimple) socket interface
resources/language/*/strings.po  localized strings (tr(id) reads these)
resources/settings.xml     addon settings
resources/icons|media/     artwork
tests/                     pytest + Kodi API stub modules
```

## Environment constraints

- The `xbmc*` modules only exist inside Kodi. Never `pip install` them; the
  fake modules in `tests/` (`xbmc.py`, `xbmcaddon.py`, ...) emulate the API for
  pytest. Keep them in sync with the real API when touching addon code.
- Target Python compatibility: **3.8 is the floor**, not 3.9. The Windows and
  Xbox builds of Kodi 20 and 21 bundle Python 3.8.15 (Kodi 22 moves to 3.12),
  and Linux builds use the system Python, which is older still (OSMC's Kodi
  21.3 runs on Python 3.9). So: no PEP 585 builtin generics evaluated at
  runtime (`list[dict]`, `dict[str, str]` need 3.9 — add `from __future__
  import annotations` to the module if you want to write them), and no PEP 604
  unions (`X | None` needs 3.10; use `Optional[X]`). `target-version = "py38"`
  and `pyupgrade.keep-runtime-typing = true` in ruff.
  Note `python --version` on a user's machine reports their system Python, not
  the interpreter Kodi bundles — do not use it to judge addon compatibility.
- Supported Kodi: the addon requires `xbmc.python 3.0.1`, which is what Kodi
  19.5, 20 and 21 ship (19.0-19.4 have 3.0.0). Note that 19.5 and 20 share the
  same `xbmc.python` version, so the requirement cannot express "20+ only" —
  that would need `3.1.0`, which is Kodi 22.
- Addon imports are module-level side-effectful (`xbmcaddon.Addon()` runs at
  import time in `resources/lib/addon.py`). Anything importing it needs the
  stub modules on `sys.path` first (see `tests/test_routing.py`, `tests/cron.py`).
- Dependencies are declared in `addon.xml` (`script.module.*`), not pip.
  Keep `tests/envs/test.yml` in sync when adding runtime deps.

## Commands

```bash
# tests (from repo root; stub modules are found via tests/)
pytest tests --disable-warnings

# lint
ruff check .

# addon metadata/xml validation
kodi-addon-checker --branch=omega --allow-folder-id-mismatch

# run a single test
pytest tests/test_routing.py::test_basemenus --disable-warnings
```

Note: `test_routing.py` tests are integration-style and read recorded HTTP
caches under `tests/userdata/`. If a cache entry is missing they hit the live
DR API and fail. Do not "fix" such failures by re-recording against the live
API without asking; prefer adding small JSON fixtures instead.

## Style

- Match the existing style of the file you are editing; formatting is not
  uniformly enforced yet (ruff config is being introduced — see
  IMPROVEMENT_PLAN.md).
- Line length up to 200 chars is accepted (matches CI flake8 config).
- Log via the existing `log()` helpers gated on the `log.debug` setting —
  never plain `print()` in `resources/lib/` code.
- User-visible strings come from `strings.po` via `tr(id)`; do not hardcode
  new user-facing strings.
- URLs are built with query strings parsed by `urllib.parse`; keep parameter
  names stable (`show=`, `listVideos=`, `playVideo=`, `area=`, `nocache=`) —
  they are part of the addon's "API" (context-menu `RunAddon(...)` scripts
  construct them too).

## Testing expectations

- New logic in `resources/lib/` should come with tests. Pure functions
  (subtitle conversion, query munging, title/area classification) need no Kodi
  stubs — put them in `tests/test_<module>.py`.
- Changes to routing/menu behavior: update the golden JSON under
  `tests/userdata/menudata/` deliberately and mention it in the commit.
- Never commit tokens, caches, or recorded credentials (`token.p`,
  `requests.cache*`, `*.srt` outputs are gitignored).

## Branches and releases

- Default branch: `master`. Work on feature branches; there are many small
  topic branches (one per fix) — that convention works well here.
- Version lives in `addon.xml` (`version=` attribute) and `changelog.txt`
  records user-visible changes. Bump both for user-facing changes.
- Tags like `v6.6.1` mark releases.

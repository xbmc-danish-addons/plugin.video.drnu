# -*- coding: utf-8 -*-
"""Shared pytest fixtures for the drnu addon tests.

Imports the Kodi API stub modules from tests/ before any addon module is
imported, since resources/lib/addon.py has module-level side effects
(xbmcaddon.Addon() at import time).
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# tests/ must be on sys.path so the stub xbmc* modules resolve
TESTS_DIR = Path(__file__).parent.resolve()
REPO_DIR = TESTS_DIR.parent

for p in (str(REPO_DIR), str(TESTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Import the stub modules before anything that pulls in the addon
import xbmc  # noqa: E402
import xbmcaddon  # noqa: E402
import xbmcgui  # noqa: E402
import xbmcplugin  # noqa: E402
import xbmcvfs  # noqa: E402
import inputstreamhelper  # noqa: E402

from resources.lib import addon  # noqa: E402

PLUGIN_URL = 'plugin://plugin.video.drnu/'

# token expiry far enough in the future that refresh_tokens() is a no-op
TOKEN_EXPIRES_HOURS = 365 * 24


def pytest_addoption(parser):
    parser.addoption(
        '--update-golden', action='store_true', default=False,
        help='Rewrite golden files under tests/userdata/menudata/')


def pytest_configure(config):
    import test_routing
    test_routing.UPDATE_TESTS = config.getoption('--update-golden')


def _anonymous_tokens():
    expires = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRES_HOURS)).strftime('%Y-%m-%dT%H:%M:%S')
    return [
        {'Token': 'test-user-token', 'Expires': expires},
        {'Token': 'test-profile-token', 'Expires': expires},
    ]


@pytest.fixture(scope='session')
def addon_handle():
    """Create a DrDkTvAddon instance serving recorded fixtures.

    The addon reads its handle through xbmcplugin stubs; tests replace
    _plugin_handle with a plain dict so added items can be inspected.
    Token refresh and the sqlite cache are disabled so no test can touch
    the network or the recorded cache files.
    """
    from fixtures_adapter import install_fake_session, install_fixture_adapter

    addon.tvapi.Api.refresh_tokens = lambda self: None
    addon.tvapi.Api.init_sqlite_db = lambda self: None
    handle = addon.DrDkTvAddon(plugin_url=PLUGIN_URL, plugin_handle=1)
    handle._plugin_handle = {}
    handle.api.read_tokens(_anonymous_tokens())
    handle.api._user_name = 'anonymous'
    install_fixture_adapter(handle)
    install_fake_session(handle)
    return handle


@pytest.fixture
def handle(addon_handle, tmp_path):
    """Fresh handle state and default settings per test."""
    addon_handle._plugin_handle = {}
    addon.addon.settings.clear()
    addon.addon.settings.update(DEFAULT_SETTINGS)
    # keep the search pickle out of the tracked userdata tree
    addon_handle.search_path = tmp_path / 'search6.pickle'
    return addon_handle


@pytest.fixture(scope='session')
def menudata_dir(addon_handle):
    """Path to the golden menu JSON files."""
    userdata = Path(addon.translatePath(addon.addon.getAddonInfo('profile')))
    menudata = userdata / 'menudata'
    menudata.mkdir(parents=True, exist_ok=True)
    return menudata


DEFAULT_SETTINGS = dict(addon.addon.settings)

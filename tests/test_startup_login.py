"""Regression tests for the startup login failure reported in issue 132.

A wrong password makes tvapi.Api.__init__ raise ApiException from
DrDkTvAddon.__init__, which default.py calls outside any try/except. The user
used to see a raw traceback and Kodi's "Error getting plugin://..." instead of
a dialog. The addon now captures the failure and reports it from route().
"""
from pathlib import Path

import pytest

from resources.lib import addon, tvapi
from resources.lib.kodiutils import get_addon

PLUGIN_URL = 'plugin://plugin.video.drnu/'


class DialogRecorder:
    """Records xbmcgui.Dialog().ok() calls instead of printing them."""

    def __init__(self):
        self.calls = []

    def ok(self, heading, message='', *args, **kwargs):
        self.calls.append((heading, message))


@pytest.fixture
def dialogs(monkeypatch):
    recorder = DialogRecorder()
    monkeypatch.setattr(addon.xbmcgui, 'Dialog', lambda: recorder)
    return recorder


@pytest.fixture
def end_of_directory(monkeypatch):
    calls = []
    monkeypatch.setattr(addon.xbmcplugin, 'endOfDirectory',
                        lambda handle, succeeded=True, **kwargs: calls.append(succeeded))
    return calls


def _addon_with_failing_login(monkeypatch, message='Login failed with: "INVALID_PASSWORD_ERROR"'):
    """Build a DrDkTvAddon whose Api construction raises, as a bad login does."""
    def failing_api(*args, **kwargs):
        raise tvapi.ApiException(message)

    monkeypatch.setattr(addon.tvapi, 'Api', failing_api)
    return addon.DrDkTvAddon(plugin_url=PLUGIN_URL, plugin_handle=1)


def test_startup_login_failure_is_captured_not_raised(monkeypatch):
    handle = _addon_with_failing_login(monkeypatch)

    assert handle.api is None
    assert isinstance(handle._startup_error, tvapi.ApiException)
    assert 'INVALID_PASSWORD_ERROR' in str(handle._startup_error)


def test_route_reports_startup_error_with_the_login_dialog(monkeypatch, dialogs, end_of_directory):
    """A configured username means the failure is a credentials problem, so the
    login dialog is shown -- the same one the interactive login route uses."""
    handle = _addon_with_failing_login(monkeypatch)
    monkeypatch.setitem(get_addon().settings, 'drtv_username', 'someuser')

    handle.route('?area=drtv')  # must not raise

    assert len(dialogs.calls) == 1
    heading, message = dialogs.calls[0]
    assert heading == '30306'
    assert message.startswith('30307')
    assert 'INVALID_PASSWORD_ERROR' in message
    assert end_of_directory == [False]


def test_route_reports_startup_error_with_the_api_dialog_when_anonymous(monkeypatch, dialogs, end_of_directory):
    """Without a username the failure is a token/transport problem, so the
    generic API error dialog applies."""
    handle = _addon_with_failing_login(monkeypatch, message='Login failed with: "HTTP 502"')
    monkeypatch.delitem(get_addon().settings, 'drtv_username', raising=False)

    handle.route('?area=drtv')  # must not raise

    assert len(dialogs.calls) == 1
    heading, message = dialogs.calls[0]
    assert heading == 'API error'
    assert 'HTTP 502' in message
    assert end_of_directory == [False]


def test_login_route_stays_reachable_after_a_startup_failure(monkeypatch, dialogs, end_of_directory):
    """The login route must not be swallowed by the startup-error guard, or the
    user could never fix the credentials."""
    handle = _addon_with_failing_login(monkeypatch)
    called = []
    monkeypatch.setattr(handle, 'login', lambda: called.append(1))

    handle.route('?loginnow=1')

    assert called == [1]
    assert dialogs.calls == []
    assert end_of_directory == []


def test_login_rebuilds_the_api_without_the_failing_refresh(monkeypatch):
    """After a startup failure, login() rebuilds the Api with refresh=False so
    request_tokens() can report the outcome itself."""
    handle = _addon_with_failing_login(monkeypatch)
    seen = {}

    class FakeApi:
        def __init__(self, cache_path, tr, get_setting, log_func, refresh=True):
            seen['refresh'] = refresh
            self.user = ''
            self.user_name = ''

        def _refresh_settings(self):
            pass

        def request_tokens(self):
            return 'bad creds'

    monkeypatch.setattr(addon.tvapi, 'Api', FakeApi)
    monkeypatch.setattr(handle, 'displayError', lambda message='': seen.setdefault('error', message))

    handle.login()

    assert seen['refresh'] is False
    assert handle._startup_error is None
    assert seen['error'] == 'bad creds'


def test_successful_startup_leaves_no_startup_error(monkeypatch):
    monkeypatch.setattr(tvapi.Api, 'refresh_tokens', lambda self: None)
    monkeypatch.setattr(tvapi.Api, 'init_sqlite_db', lambda self: None)

    handle = addon.DrDkTvAddon(plugin_url=PLUGIN_URL, plugin_handle=1)

    assert handle._startup_error is None
    assert handle.api is not None


def test_api_init_refresh_false_skips_the_token_refresh(monkeypatch):
    """refresh=False is what lets login() build an Api after a failed startup
    login without raising the same error again."""
    def must_not_refresh(self):
        raise AssertionError('refresh_tokens must not run with refresh=False')

    monkeypatch.setattr(tvapi.Api, 'init_sqlite_db', lambda self: None)
    monkeypatch.setattr(tvapi.Api, 'refresh_tokens', must_not_refresh)

    api = tvapi.Api(Path('/tmp'), lambda i: '', get_addon().getSetting, refresh=False)

    assert api._user_token is None

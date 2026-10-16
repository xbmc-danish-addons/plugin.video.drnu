"""Regression tests for the two crashes reported in issue 132.

Both surfaced as a TypeError instead of a clear failure:

1. A failed token request could carry an empty 'error' (res.text is empty for
   some failures, e.g. a 502 from a proxy). The callers test the error for
   truthiness, so an empty one read as success and left the token as None,
   which then crashed on 'Bearer ' + None in get_profile()/get_stream().
2. The Windows and Xbox builds of Kodi 20/21 bundle Python 3.8, where the
   PEP 585 annotations (list[dict], dict[str, str]) in tvapi/gui/subtitles/
   recachescheduler are not subscriptable at import time. The reporter saw
   this on Kodi 21.3 Omega for Windows.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from resources.lib import drauth, gui, recachescheduler, subtitles, tvapi

# conftest's addon_handle fixture patches Api.refresh_tokens class-wide to a
# no-op; keep the real one so this module can exercise it
_REAL_REFRESH_TOKENS = tvapi.Api.refresh_tokens

_ANNOTATED_MODULES = (subtitles, tvapi, gui, recachescheduler)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, content=b'', url='https://x/', text=''):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.content = content
        self.text = text
        self.url = url

    def json(self):
        return self._json


class FakeRequests:
    """Stands in for the requests module, returning queued responses in order."""

    def __init__(self, responses):
        self.responses = list(responses)

    def _next(self):
        return self.responses.pop(0)

    def get(self, *args, **kwargs):
        return self._next()

    def post(self, *args, **kwargs):
        return self._next()

    def Session(self):  # noqa: N802 - mirrors requests.Session
        return self


# --- an empty error body must not read as success ---------------------------

def test_http_error_falls_back_to_status_when_body_is_empty():
    err = drauth._http_error(FakeResponse(status_code=502, text=''), 'Anonymous token request')
    assert err['status_code'] == 502
    assert err['error']  # never empty: 'if err:' would read as success


def test_http_error_keeps_the_body_when_present():
    err = drauth._http_error(FakeResponse(status_code=403, text='  forbidden  '), 'Login')
    assert err['error'] == 'forbidden'


def test_oidc_token_error_is_never_empty(monkeypatch):
    monkeypatch.setattr(drauth, 'requests', FakeRequests([FakeResponse(status_code=502, text='')]))
    assert drauth.oidc_token({})['error'] == 'Token request failed with HTTP 502'


def test_anonymous_tokens_error_is_never_empty(monkeypatch):
    monkeypatch.setattr(drauth, 'requests', FakeRequests([FakeResponse(status_code=429, text='')]))
    assert drauth.anonymous_tokens()['error'] == 'Anonymous token request failed with HTTP 429'


def test_exchange_token_error_is_never_empty(monkeypatch):
    monkeypatch.setattr(drauth, 'requests', FakeRequests([FakeResponse(status_code=500, text='')]))
    err = drauth.exchange_token({'access_token': 'a', 'id_token': 'i'})
    assert err['error'] == 'Token exchange failed with HTTP 500'


def test_login_error_with_empty_message_falls_back_to_the_code(monkeypatch):
    """A GraphQL Error with message='' must not yield an empty error."""
    responses = [
        FakeResponse(url='https://login.dr.dk/oidc/authorize/trans123'),
        FakeResponse(json_data={}),
        FakeResponse(json_data={}),
        FakeResponse(json_data={'data': {'authenticate': {'__typename': 'Error',
                                                          'code': 'AUTHENTICATION_FAILED',
                                                          'message': ''}}}),
    ]
    monkeypatch.setattr(drauth, 'requests', FakeRequests(responses))
    assert drauth.full_login('user', 'wrong')['error'] == 'AUTHENTICATION_FAILED'


def _token_api(user='', access_tokens=None):
    api = tvapi.Api.__new__(tvapi.Api)
    api.user = user
    api.password = 'pw'
    api.log = None
    api.cachePath = None
    api.token_file = Path('/nonexistent/token.p')
    api.access_tokens = access_tokens if access_tokens is not None else {}
    api._user_token = None
    api._profile_token = None
    api._user_name = ''
    api.tr = lambda i: ''
    return api


def test_request_tokens_surfaces_the_endpoint_error(monkeypatch):
    """request_tokens passes the endpoint's error through; drauth guarantees it
    is never empty, and refresh_tokens refuses to treat a falsy one as success
    (covered below)."""
    api = _token_api()
    monkeypatch.setattr(tvapi, 'anonymous_tokens', lambda: {'status_code': 502, 'error': 'upstream down'})
    assert api.request_tokens() == 'upstream down'


def test_refresh_tokens_raises_instead_of_leaving_profile_token_none(monkeypatch):
    """The issue-132 crash: a failed token request used to leave the profile
    token None, and the caller then did 'Bearer ' + None."""
    api = _token_api()
    monkeypatch.setattr(tvapi, 'anonymous_tokens', lambda: {'status_code': 502, 'error': ''})

    with pytest.raises(tvapi.ApiException, match='Login failed'):
        _REAL_REFRESH_TOKENS(api)

    assert api._profile_token is None  # never handed out as a usable token


def test_refresh_tokens_raises_for_a_falsy_error_from_request_tokens(monkeypatch):
    """Defence in depth: even if request_tokens returns a falsy error, the
    caller must not treat it as success."""
    api = _token_api()
    api.request_tokens = lambda: ''
    with pytest.raises(tvapi.ApiException, match='Login failed'):
        _REAL_REFRESH_TOKENS(api)


def test_refresh_tokens_raises_for_a_falsy_refresh_error(monkeypatch):
    """A refresh grant that fails with an empty error must fall back to a fresh
    login and raise if that fails too, not read the error dict as a token list."""
    api = _token_api(user='user', access_tokens={'refresh_token': 'r'})
    api._user_token = 'old'  # present, so refresh takes the expiry branch
    api._token_expire = datetime.now(timezone.utc) - timedelta(hours=1)
    api.read_tokens = lambda tokens: None
    api.write_tokens = lambda tokens: None
    monkeypatch.setattr(tvapi, 'refresh_token', lambda rt: {'error': ''})
    monkeypatch.setattr(tvapi, 'full_login', lambda u, p, log=None: {'status_code': 403, 'error': 'bad creds'})

    with pytest.raises(tvapi.ApiException, match='Login failed with: "bad creds"'):
        _REAL_REFRESH_TOKENS(api)


def test_get_profile_no_longer_concatenates_none_after_a_failed_login(monkeypatch):
    """End-to-end for the reported traceback: gui.main_menu_items asks for
    api.user_name, which asks get_profile for the name."""
    api = _token_api()
    api._request_get = lambda url, params=None, headers=None, use_cache=True: {'name': 'Hans'}
    # conftest patches Api.refresh_tokens class-wide to a no-op; this test needs
    # the real one, or profile_token() would silently return None
    monkeypatch.setattr(tvapi.Api, 'refresh_tokens', _REAL_REFRESH_TOKENS)
    monkeypatch.setattr(tvapi, 'anonymous_tokens', lambda: {'status_code': 502, 'error': ''})

    with pytest.raises(tvapi.ApiException, match='Login failed'):
        api.user_name


def test_get_profile_still_works_with_a_valid_token(monkeypatch):
    expiry = (datetime.now(timezone.utc) + timedelta(hours=100)).strftime('%Y-%m-%dT%H:%M:%S')
    api = _token_api()
    api.read_tokens([{'Expires': expiry, 'Token': 'u'}, {'Expires': expiry, 'Token': 'p'}])
    monkeypatch.setattr(tvapi.Api, 'refresh_tokens', _REAL_REFRESH_TOKENS)
    seen = {}

    def fake_get(url, params=None, headers=None, use_cache=True):
        seen['auth'] = headers['X-Authorization']
        return {'name': 'Hans'}

    api._request_get = fake_get
    assert api.user_name == 'Hans'
    assert seen['auth'] == 'Bearer p'


# --- the addon must import on the Python 3.8 that Kodi 20/21 ship on Windows --

def test_pep585_annotations_are_deferred_to_strings():
    """`from __future__ import annotations` in the annotated modules keeps the
    annotations as strings, so the PEP 585 forms are never evaluated at import
    time (which raised 'type' object is not subscriptable on Python 3.8)."""
    assert subtitles.handle_subtitle_vtts.__annotations__['return'] == 'dict[str, str]'
    assert subtitles.handle_subtitle_vtts.__annotations__['subs'] == 'list[dict]'
    assert gui.main_menu_items.__annotations__['menu_items'] == 'list[tuple[str, str]]'
    assert tvapi.Api.read_tokens.__annotations__['tokens'] == 'list[dict]'
    assert recachescheduler.parse_time_setting.__annotations__['return'] == 'Optional[time]'


@pytest.mark.parametrize('module', _ANNOTATED_MODULES, ids=lambda m: m.__name__.rsplit('.', 1)[-1])
def test_annotations_are_never_evaluated_at_import(module):
    """PEP 563 turns every annotation into a string, so the PEP 585 forms are
    never evaluated at import time -- which is what raised 'type' object is not
    subscriptable on Python 3.8. Functions defined in these modules must
    therefore carry string annotations, not evaluated objects."""
    for func in vars(module).values():
        annotations = getattr(func, '__annotations__', None)
        if not annotations or getattr(func, '__module__', None) != module.__name__:
            # re-exported (e.g. the drauth functions in tvapi) keep their own
            # module's annotations, which are plain types, not subscripts
            continue
        for name, annotation in annotations.items():
            assert isinstance(annotation, str), \
                f'{module.__name__}.{func.__name__}: {name} = {annotation!r}'

"""Tests for the cache-bypass and error-handling review fixes in tvapi.

search() and get_stream() must never serve cached responses: a search must
reflect the term the user just typed, and a stream URL carries a signed
playback token that goes stale. Both bypass the cache while still using the
session, so its retry adapter stays in play. request_tokens() must check the
token endpoints' error dicts before treating the result as a token list.
"""
from resources.lib import tvapi

# conftest's addon_handle fixture patches Api.refresh_tokens class-wide to a
# no-op; capture the real one so this module can exercise it
_REAL_REFRESH_TOKENS = tvapi.Api.refresh_tokens


class _CacheDisabled:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        self.session.cache_disabled_used += 1
        return self

    def __exit__(self, *exc):
        return False


class FakeResponse:
    def __init__(self, js, status_code=200):
        self.status_code = status_code
        self._json = js

    def json(self):
        return self._json


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.cache_disabled_used = 0

    def cache_disabled(self):
        return _CacheDisabled(self)

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({'url': url, 'params': dict(params) if params else params})
        return self.responses.pop(0)


def _api(session):
    api = tvapi.Api.__new__(tvapi.Api)
    api.session = session
    api.profile_token = lambda: 'ptoken'
    api.user_token = lambda: 'utoken'
    api.tr = lambda i: ''
    api.cachePath = None
    return api


def test_search_bypasses_the_cache():
    video = {'series': {'size': 0, 'items': []}}
    session = FakeSession([FakeResponse(video)])
    assert _api(session).search('bluey') == video
    assert session.cache_disabled_used == 1
    assert session.calls[0]['url'] == tvapi.URL + '/search'


def test_get_stream_bypasses_the_cache():
    streams = [{'accessService': 'StandardVideo', 'subtitles': [], 'url': 'https://x/v.m3u8'}]
    session = FakeSession([FakeResponse(streams)])
    stream = _api(session).get_stream(123)
    assert stream['url'] == 'https://x/v.m3u8'
    assert session.cache_disabled_used == 1


def test_get_stream_retries_without_registered_when_unauthorized():
    """A non-200 on the registered request must retry anonymously, still
    uncached."""
    streams = [{'accessService': 'StandardVideo', 'subtitles': [], 'url': 'https://x/v.m3u8'}]
    session = FakeSession([FakeResponse('nope', status_code=401), FakeResponse(streams)])
    assert _api(session).get_stream(123)['url'] == 'https://x/v.m3u8'
    assert session.cache_disabled_used == 1
    assert session.calls[0]['params']['sub'] == 'Registered'
    assert 'sub' not in session.calls[1]['params']


def _token_api(user):
    api = tvapi.Api.__new__(tvapi.Api)
    api.user = user
    api.password = 'pw'
    api.log = None
    api.access_tokens = {}
    api._user_token = None
    api._profile_token = None
    api.read_tokens = lambda tokens: setattr(api, 'read', tokens)
    api.write_tokens = lambda tokens: setattr(api, 'written', tokens)
    return api


def test_request_tokens_returns_exchange_error(monkeypatch):
    """exchange_token can fail after a successful login; the error must be
    returned, not passed to read_tokens where tokens[0] would KeyError."""
    api = _token_api('user')
    monkeypatch.setattr(tvapi, 'full_login', lambda u, p, log=None: {'access_token': 'a', 'id_token': 'i'})
    monkeypatch.setattr(tvapi, 'exchange_token', lambda tokens: {'status_code': 500, 'error': 'exchange down'})
    assert api.request_tokens() == 'exchange down'
    assert not hasattr(api, 'read')


def test_request_tokens_returns_anonymous_error(monkeypatch):
    api = _token_api('')
    monkeypatch.setattr(tvapi, 'anonymous_tokens', lambda: {'status_code': 500, 'error': 'anon down'})
    assert api.request_tokens() == 'anon down'
    assert not hasattr(api, 'read')


def test_request_tokens_reads_a_valid_token_list(monkeypatch):
    api = _token_api('')
    monkeypatch.setattr(tvapi, 'anonymous_tokens', lambda: [{'Token': 't'}, {'Token': 'p'}])
    assert api.request_tokens() is None
    assert api.read == [{'Token': 't'}, {'Token': 'p'}]
    assert api.written == [{'Token': 't'}, {'Token': 'p'}]


def test_refresh_tokens_falls_back_when_exchange_fails(monkeypatch, tmp_path):
    """A failed token exchange during refresh must retry request_tokens()
    rather than read the error dict as tokens."""
    from datetime import datetime, timedelta, timezone
    api = tvapi.Api.__new__(tvapi.Api)
    api._user_token = 'old'  # present, so refresh takes the expiry branch
    api.user = 'user'
    api.password = 'pw'
    api.log = None
    api.access_tokens = {'refresh_token': 'r'}
    api.token_file = tmp_path / 'token.p'  # absent, so the cache path is skipped
    api._token_expire = datetime.now(timezone.utc) - timedelta(hours=1)
    api.read_tokens = lambda tokens: None
    api.write_tokens = lambda tokens: None
    request_calls = []

    def request_tokens():
        request_calls.append(True)
        api._user_token = 'fresh'
        return None

    api.request_tokens = request_tokens
    monkeypatch.setattr(tvapi, 'refresh_token', lambda rt: {'access_token': 'a', 'id_token': 'i'})
    monkeypatch.setattr(tvapi, 'exchange_token', lambda tokens: {'status_code': 500, 'error': 'nope'})

    _REAL_REFRESH_TOKENS(api)
    assert request_calls == [True]
    assert api._user_token == 'fresh'

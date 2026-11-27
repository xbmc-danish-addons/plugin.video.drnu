"""Hermetic request adapter: serves recorded JSON fixtures instead of live HTTP.

Replaces Api._request_get with a function that looks up the request in
tests/fixtures/_index.json (built from the tracked requests.cache.sqlite db)
and returns the stored JSON body. Fails loudly on a cache miss instead of
silently hitting the live DR API.

get_next() strips lang/segments/isDeviceAbroad/isLive2VodSupported from
next-page URLs before requesting them, while the recorded cache URLs carry
them — so keys are matched on the stripped form, and a 'page=1' fallback key
covers requests where the addon does not send the explicit page param.
"""
import contextlib
import json
import urllib.parse as urlparse
from pathlib import Path

FIXTURES = Path(__file__).parent / 'fixtures'

STRIP_KEYS = ['lang', 'segments', 'isDeviceAbroad', 'isLive2VodSupported']


class FixtureMiss(Exception):
    """Raised when a request has no recorded fixture — tests must not hit the live API."""


def fixture_key(url, params=None):
    """Normalized fixture key: path + sorted params, minus paging-context params."""
    u = urlparse.urlsplit(url)
    q = dict(urlparse.parse_qsl(u.query, keep_blank_values=True))
    if params:
        q.update({str(k): str(v) for k, v in params.items()})
    for k in STRIP_KEYS:
        q.pop(k, None)
    if q.get('page') == '1':
        del q['page']
    return u.path + '?' + urlparse.urlencode(sorted(q.items()))


def load_index():
    return json.loads((FIXTURES / '_index.json').read_text(encoding='utf-8'))


def _read_fixture(index, key):
    if key not in index:
        raise FixtureMiss(f'no fixture for {key}\nAdd it to tests/fixtures/ (record with --update-golden)')
    data = json.loads((FIXTURES / index[key]).read_text(encoding='utf-8'))
    if data['status'] != 200:
        raise AssertionError(f'fixture for {key} has status {data["status"]}')
    return data['json']


def install_fixture_adapter(handle):
    """Patch handle.api._request_get to serve fixtures."""
    index = load_index()

    def request_get(url, params=None, headers=None, use_cache=True):
        key = fixture_key(url, params)
        try:
            return _read_fixture(index, key)
        except FixtureMiss:
            if 'page=1&' not in key + '&' and not key.endswith('?page=1'):
                raise
            # get_list() sends page=1 explicitly; the recorded first page
            # does not carry it — retry without the page param
            q = urlparse.urlsplit('?' + key.split('?', 1)[1])
            fallback = dict(urlparse.parse_qsl(q.query))
            fallback.pop('page', None)
            return _read_fixture(index, q.path + '?' + urlparse.urlencode(sorted(fallback.items())))

    handle.api._request_get = request_get
    return request_get


def install_recording_adapter(handle):
    """Record live responses into tests/fixtures instead of serving them.

    Writes one JSON file per distinct request key (same key function the
    replay adapter uses, so a recorded run replays exactly) and rewrites
    _index.json at the end. Only for re-recording the suite deliberately;
    it talks to the live DR API.
    """
    import hashlib
    import requests

    recorded = {}

    def request_get(url, params=None, headers=None, use_cache=True):
        key = fixture_key(url, params)
        response = requests.get(url, params=params, headers=headers, timeout=30)
        name = hashlib.md5(key.encode('utf-8')).hexdigest()[:16] + '.json'
        (FIXTURES / name).write_text(
            json.dumps({'status': response.status_code, 'json': response.json()},
                       indent=1, ensure_ascii=False),
            encoding='utf-8')
        recorded[key] = name
        return response.json()

    def write_index():
        index_path = FIXTURES / '_index.json'
        existing = json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else {}
        existing.update(recorded)
        index_path.write_text(json.dumps(existing, indent=1, sort_keys=True, ensure_ascii=False),
                              encoding='utf-8')
        return len(recorded)

    handle.api._request_get = request_get
    return write_index


class FakeSession:
    """Stands in for the requests-cache session: subtitle downloads call
    session.get, and search()/get_stream() wrap their call in
    session.cache_disabled()."""

    def __init__(self, index):
        self._index = index

    def cache_disabled(self):
        return contextlib.nullcontext()

    def get(self, url, params=None, headers=None, timeout=None):
        key = fixture_key(url, params)
        return FakeResponse(_read_fixture(self._index, key))


class FakeResponse:
    def __init__(self, js):
        self.status_code = 200
        self._json = js

    def json(self):
        return self._json


def install_fake_session(handle):
    """Route subtitle downloads' direct session.get calls through the fixtures."""
    handle.api.session = FakeSession(load_index())


class RecordingSession:
    """A session whose get() records live responses in the fixture store.

    search() and get_stream() bypass the request cache through the session,
    so re-recording needs a session that writes to the same store as the
    recording adapter.
    """

    def __init__(self, request_get):
        self._request_get = request_get

    def cache_disabled(self):
        return contextlib.nullcontext()

    def get(self, url, params=None, headers=None, timeout=None):
        return FakeResponse(self._request_get(url, params=params, headers=headers, use_cache=False))


def install_recording_session(handle, request_get):
    handle.api.session = RecordingSession(request_get)

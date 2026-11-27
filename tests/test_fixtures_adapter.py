"""Unit tests for the fixture adapter key normalization."""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent))

import fixtures_adapter  # noqa: E402
from fixtures_adapter import FakeResponse, fixture_key  # noqa: E402


def test_key_sorts_params():
    assert fixture_key('https://x.dk/api/lists/348?page_size=24&page=2&param=a') == \
        fixture_key('https://x.dk/api/lists/348?page=2&page_size=24&param=a')


def test_key_strips_paging_context_params():
    # get_next() strips these before requesting; recorded URLs carry them
    key = fixture_key(
        'https://x.dk/api/lists/348?page_size=24&page=2&param=a'
        '&lang=da&segments=DRTV,minisjang,ramasjang,ultra&isDeviceAbroad=false&isLive2VodSupported=true')
    assert key == '/api/lists/348?page=2&page_size=24&param=a'


def test_key_drops_explicit_first_page():
    assert fixture_key('https://x.dk/api/lists/348?page=1&page_size=24&param=a') == \
        fixture_key('https://x.dk/api/lists/348?page_size=24&param=a')


def test_key_includes_params_argument():
    key = fixture_key('https://x.dk/api/lists/348', params={'page_size': '24', 'param': 'TitleGroupKey:a'})
    assert key == '/api/lists/348?page_size=24&param=TitleGroupKey%3Aa'


def test_fake_response_json():
    assert FakeResponse({'a': 1}).json() == {'a': 1}
    assert FakeResponse({}).status_code == 200


def test_fixture_key_strips_the_web_params_and_sorts():
    """The adapter keys on path + sorted params minus the paging context, so a
    recorded run replays exactly. WEB_PARAMS are stripped because get_next()
    removes them before asking for a later page."""
    from fixtures_adapter import fixture_key
    from resources.lib import tvapi

    key = fixture_key(tvapi.URL + '/page', {'path': '/', 'segments': 'drtv,optedin',
                                            'lang': 'da', 'list_page_size': 24})
    assert key == '/api/page?list_page_size=24&path=%2F'


def test_recorded_index_entries_all_exist():
    """Every key in _index.json must point at a fixture file, or a replay run
    fails on a missing file instead of a missing key."""
    from fixtures_adapter import FIXTURES, load_index

    index = load_index()
    assert index
    missing = [name for name in index.values() if not (FIXTURES / name).is_file()]
    assert missing == []


class _LiveResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data
        self.text = str(json_data)

    def json(self):
        return self._json


def _record(monkeypatch, tmp_path, status_code):
    """Wire install_recording_adapter to a temp fixture dir and a fake live API."""
    monkeypatch.setattr(fixtures_adapter, 'FIXTURES', tmp_path)
    monkeypatch.setattr(requests, 'get',
                        lambda *a, **kw: _LiveResponse(status_code, {'error': 'rate limited'}))

    class Handle:
        api = type('api', (), {})()

    return Handle, fixtures_adapter.install_recording_adapter(Handle)


def test_recording_writes_a_successful_response(monkeypatch, tmp_path):
    handle, write_index = _record(monkeypatch, tmp_path, status_code=200)

    assert handle.api._request_get('https://x.dk/api/page', params={'path': '/'}) == {'error': 'rate limited'}
    assert write_index() == 1
    assert len([p for p in tmp_path.glob('*.json') if p.name != '_index.json']) == 1


def test_recording_skips_a_failed_request(monkeypatch, tmp_path):
    """A non-200 response must not be written: it would replace a working
    fixture and enter the index, and _read_fixture() rejects anything but
    status 200, so every later replay of that key would fail."""
    handle, _ = _record(monkeypatch, tmp_path, status_code=429)

    with pytest.raises(AssertionError, match='status 429'):
        handle.api._request_get('https://x.dk/api/page', params={'path': '/'})

    assert list(tmp_path.glob('*.json')) == []

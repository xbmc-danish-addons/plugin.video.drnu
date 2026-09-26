"""Unit tests for the fixture adapter key normalization."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

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

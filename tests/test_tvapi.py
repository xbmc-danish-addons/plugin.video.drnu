"""Unit tests for pure functions in resources/lib/tvapi.py (no Kodi needed)."""
from resources.lib import tvapi


def test_fix_query_add_and_sort():
    url = tvapi.fix_query('https://x.dk/api/page?path=/kategorier/a-aa', add={'lang': 'da'})
    assert url == 'https://x.dk/api/page?lang=da&path=%2Fkategorier%2Fa-aa'


def test_fix_query_remove_keys():
    url = tvapi.fix_query(
        'https://x.dk/api/lists/348?page_size=24&param=TitleGroupKey%3Aa&lang=da&page=2',
        remove_keys=['lang'])
    assert url == 'https://x.dk/api/lists/348?page=2&page_size=24&param=TitleGroupKey%3Aa'


def test_fix_query_remove_matching_value_only():
    url = tvapi.fix_query('https://x.dk/api/page?sub=Registered&x=1', remove={'sub': 'Emergency'})
    assert url == 'https://x.dk/api/page?sub=Registered&x=1'
    url = tvapi.fix_query('https://x.dk/api/page?sub=Emergency&x=1', remove={'sub': 'Emergency'})
    assert url == 'https://x.dk/api/page?x=1'


def test_fix_query_no_query():
    url = tvapi.fix_query('https://x.dk/api/page', add={'page_size': '24'})
    assert url == 'https://x.dk/api/page?page_size=24'


def test_get_title_plain():
    assert tvapi.Api.get_title(None, {'title': 'Casper', 'type': 'episode'}) == 'Casper'


def test_get_title_season_number():
    item = {'title': 'Casper', 'type': 'season', 'seasonNumber': 2}
    assert tvapi.Api.get_title(None, item) == 'Casper 2'


def test_get_title_contextual():
    item = {'title': 'Casper', 'type': 'program', 'contextualTitle': '2. Del'}
    assert tvapi.Api.get_title(None, item) == 'Casper (2. Del)'
    # contextual part already in the title is not appended
    item = {'title': '2. Del', 'type': 'program', 'contextualTitle': '2. Del'}
    assert tvapi.Api.get_title(None, item) == '2. Del'


def test_item_area():
    assert tvapi.Api.item_area(None, {'classification': {'code': 'DR-Ramasjang'}}) == 'ramasjang'
    assert tvapi.Api.item_area(None, {'categories': ['DR Ultra']}) == 'ultra'
    assert tvapi.Api.item_area(None, {'categories': ['Dokumentar']}) == 'drtv'
    assert tvapi.Api.item_area(None, {}) == 'drtv'


def test_kids_item():
    assert tvapi.Api.kids_item(None, {'classification': {'code': 'DR-Ramasjang'}})
    assert tvapi.Api.kids_item(None, {'classification': {'code': 'DR-Minisjang'}})
    assert tvapi.Api.kids_item(None, {'categories': ['dr ramasjang']})
    assert not tvapi.Api.kids_item(None, {'classification': {'code': 'DR-DRTV'}})
    assert not tvapi.Api.kids_item(None, {'categories': ['Dokumentar']})
    assert not tvapi.Api.kids_item(None, {})


def test_cache_path():
    assert tvapi.cache_path('/kategorier/a-aa')
    assert tvapi.cache_path('/serie/bluey_227278')
    assert not tvapi.cache_path('/liste/drtv-hero')
    assert not tvapi.cache_path('/liste/drtv-hero-saturday-18_00_89366')


def test_schedule_windows_single_request():
    # durations <= 24 never reach _schedule_windows (single request branch)
    assert tvapi.Api._schedule_windows(6) == [(0, 6)]


def test_schedule_windows_full_days():
    assert tvapi.Api._schedule_windows(48) == [(0, 24), (1, 24)]


def test_schedule_windows_partial_tail():
    assert tvapi.Api._schedule_windows(50) == [(0, 24), (1, 24), (2, 2)]
    assert tvapi.Api._schedule_windows(167) == [(i, 24) for i in range(6)] + [(6, 23)]


def test_get_continue_reads_positions_from_watched_endpoint(monkeypatch):
    """Resume positions come from /account/profile/watched, not /account/profile."""
    api = tvapi.Api.__new__(tvapi.Api)
    api.profile_token = lambda: 'ptoken'
    api.caching = False

    def fake_get(url, params=None, headers=None, use_cache=True):
        if url.endswith('/continue-watching/list'):
            return {'items': [{'id': '100'}, {'id': '200'}, {'id': '300'}],
                    'paging': {'page': 1, 'total': 1}}
        if url.endswith('/account/profile/watched'):
            return {'100': {'position': 541}, '200': {'position': 0}}
        raise AssertionError(f'unexpected url {url}')

    api._request_get = fake_get
    api.unfold_list = lambda item, headers=None, use_cache=True: item['items']

    items = api.get_continue()
    assert [i['ResumeTime'] for i in items] == [541.0, 0.0, 0.0]


def _api_without_kodi():
    api = tvapi.Api.__new__(tvapi.Api)
    api.profile_token = lambda: 'ptoken'
    return api


def test_get_mylist_unfolds_with_the_same_use_cache(monkeypatch):
    """Later saved-list pages must not be served stale from the cache while
    page one is fetched fresh: unfold_list has to inherit use_cache."""
    api = _api_without_kodi()
    seen = {}

    def fake_get(url, params=None, headers=None, use_cache=True):
        return {'items': [{'id': 1}], 'paging': {'page': 1, 'total': 2}}

    def fake_unfold(item, headers=None, use_cache=True):
        seen['use_cache'] = use_cache
        return item['items']

    api._request_get = fake_get
    api.unfold_list = fake_unfold
    assert api.get_mylist(use_cache=False) == [{'id': 1, 'in_mylist': True}]
    assert seen['use_cache'] is False


def test_get_continue_unfolds_with_the_same_use_cache(monkeypatch):
    api = _api_without_kodi()
    seen = {}

    def fake_get(url, params=None, headers=None, use_cache=True):
        if url.endswith('/watched'):
            return {}
        return {'items': [{'id': 1}], 'paging': {'page': 1, 'total': 2}}

    def fake_unfold(item, headers=None, use_cache=True):
        seen['use_cache'] = use_cache
        return item['items']

    api._request_get = fake_get
    api.unfold_list = fake_unfold
    api.get_continue(use_cache=False)
    assert seen['use_cache'] is False


def test_unfold_list_passes_use_cache_to_every_get_next_page():
    """Both get_next calls (first 'next' page and the loop) must honour the
    caller's use_cache, or a fresh first page mixes with cached later pages."""
    api = _api_without_kodi()
    api.progress_prc = 10
    api.msg = ''
    calls = []

    def fake_get_next(path, use_cache=True, headers=None):
        calls.append(use_cache)
        return {'items': [{'id': len(calls)}],
                'paging': {'next': f'/next/{len(calls)}'} if len(calls) < 2 else {}}

    api.get_next = fake_get_next
    item = {'items': [{'id': 0}], 'paging': {'next': '/next/0', 'page': 1, 'total': 3}}
    items = api.unfold_list(item, use_cache=False)
    assert len(items) == 3
    assert calls == [False, False]



def test_schedule_windows_caps_at_seven_days():
    # a tail that would need an 8th day is dropped, like the old loop
    assert tvapi.Api._schedule_windows(168) == [(i, 24) for i in range(7)]
    assert tvapi.Api._schedule_windows(169) == [(i, 24) for i in range(7)]
    assert tvapi.Api._schedule_windows(200) == [(i, 24) for i in range(7)]

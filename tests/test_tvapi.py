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
    api.unfold_list = lambda item, headers=None: item['items']

    items = api.get_continue()
    assert [i['ResumeTime'] for i in items] == [541.0, 0.0, 0.0]



def test_schedule_windows_caps_at_seven_days():
    # a tail that would need an 8th day is dropped, like the old loop
    assert tvapi.Api._schedule_windows(168) == [(i, 24) for i in range(7)]
    assert tvapi.Api._schedule_windows(169) == [(i, 24) for i in range(7)]
    assert tvapi.Api._schedule_windows(200) == [(i, 24) for i in range(7)]


def _desc_api(fetch_full_plot=True):
    api = tvapi.Api.__new__(tvapi.Api)
    api.fetch_full_plot = fetch_full_plot
    api.log = None
    return api


def _capped_item(iid):
    return {'id': iid, 'type': 'program', 'shortDescription': 'x' * 255}


def test_needs_description_only_for_capped_items():
    api = _desc_api()
    assert api._needs_description(_capped_item(1))
    # short plot, or a plot already present, needs no detail call
    assert not api._needs_description({'id': 2, 'shortDescription': 'short'})
    assert not api._needs_description({'id': 3, 'shortDescription': 'x' * 255, 'description': 'full'})
    assert not api._needs_description({'id': 4})


def test_resolve_descriptions_fetches_only_capped_items_and_merges():
    api = _desc_api()
    fetched = []

    def get_item(iid, use_cache=True):
        fetched.append(iid)
        return {'id': iid, 'description': f'full {iid}'}

    api.get_item = get_item
    items = [
        {'id': 1, 'shortDescription': 'short'},           # no fetch
        _capped_item(2),                                   # fetch
        {'id': 3, 'shortDescription': 'x' * 255, 'description': 'already'},  # no fetch
        _capped_item(4),                                   # fetch
    ]
    api.resolve_descriptions(items)

    assert sorted(fetched) == [2, 4]
    assert items[1]['description'] == 'full 2'
    assert items[3]['description'] == 'full 4'
    assert 'description' not in items[0]
    # the truncated shortDescription and other fields are left intact
    assert items[1]['shortDescription'] == 'x' * 255


def test_resolve_descriptions_keeps_list_fields_like_resumetime():
    api = _desc_api()
    api.get_item = lambda iid, use_cache=True: {'id': iid, 'description': 'full'}
    item = _capped_item(7)
    item['ResumeTime'] = 541.0
    item['in_mylist'] = True
    api.resolve_descriptions([item])
    assert item['description'] == 'full'
    assert item['ResumeTime'] == 541.0
    assert item['in_mylist'] is True


def test_resolve_descriptions_skips_when_full_plot_disabled():
    api = _desc_api(fetch_full_plot=False)
    api.get_item = lambda iid, use_cache=True: (_ for _ in ()).throw(AssertionError('no fetch expected'))
    item = _capped_item(1)
    api.resolve_descriptions([item])
    assert 'description' not in item


def test_resolve_descriptions_tolerates_fetch_failure():
    api = _desc_api()
    logged = []
    api.log = logged.append

    def get_item(iid, use_cache=True):
        if iid == 2:
            raise tvapi.ApiException('503')
        return {'id': iid, 'description': 'full'}

    api.get_item = get_item
    items = [_capped_item(1), _capped_item(2), _capped_item(3)]
    api.resolve_descriptions(items)

    assert items[0]['description'] == 'full'
    assert 'description' not in items[1]   # failed item left as-is
    assert items[2]['description'] == 'full'
    assert len(logged) == 1 and '2' in logged[0]


def test_resolve_descriptions_stops_early_when_canceled():
    api = _desc_api()
    fetched = []
    api.get_item = lambda iid, use_cache=True: fetched.append(iid) or {'id': iid, 'description': 'full'}

    class Canceled:
        def iscanceled(self):
            return True

    api.resolve_descriptions([_capped_item(1)], progress=Canceled())
    assert fetched == []


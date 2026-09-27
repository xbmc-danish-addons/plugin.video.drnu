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

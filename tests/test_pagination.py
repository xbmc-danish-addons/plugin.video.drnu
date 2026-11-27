"""Tests for pagination in list_entries and search results.

Listings used to stop at the first page (page size 24), hiding later videos.
Both paths must follow the remaining pages via unfold_list, which the other
listing branches already did.
"""


def test_list_entries_unfolds_episode_pages(handle, monkeypatch):
    """The single-season branch must expand the episode list, not slice its
    first page."""
    season = {
        'type': 'season',
        'show': {'availableSeasonCount': 1},
        'episodes': {'items': [{'id': 1, 'type': 'episode'}],
                     'paging': {'page': 1, 'total': 1}},
    }
    monkeypatch.setattr(handle.api, 'get_programcard', lambda path, **k: {'item': season})
    unfolded = []
    monkeypatch.setattr(handle.api, 'unfold_list',
                        lambda item, **k: unfolded.append(item) or [{'id': 1, 'type': 'episode'}])
    listed = []
    monkeypatch.setattr(handle, 'listEpisodes', lambda items, **k: listed.append(items))

    handle.list_entries('/serie/bluey_227278')

    assert unfolded == [season['episodes']]
    assert listed == [[{'id': 1, 'type': 'episode'}]]


def test_searchresult_unfolds_pages(handle, monkeypatch, tmp_path):
    import pickle
    search_path = tmp_path / 'search6.pickle'
    section = {'items': [{'id': 1, 'type': 'episode'}], 'paging': {'page': 1, 'total': 3}}
    with search_path.open('wb') as fh:
        pickle.dump({'series': section}, fh)
    handle.search_path = search_path

    unfolded = []
    monkeypatch.setattr(handle.api, 'unfold_list',
                        lambda item, **k: unfolded.append(item) or [{'id': 1, 'type': 'episode'}])
    listed = []
    monkeypatch.setattr(handle, 'listEpisodes', lambda items, **k: listed.append(items))

    handle.route('?searchresult=series')

    assert unfolded == [section]
    assert listed == [[{'id': 1, 'type': 'episode'}]]


def test_list_entries_threads_no_caching_to_later_pages(handle, monkeypatch):
    """Opening a series without caching must stay uncached for the later
    requests too, or fresh episodes mix with stale cached ones."""
    season = {
        'type': 'season',
        'show': {'availableSeasonCount': 1},
        'episodes': {'items': [{'id': 1, 'type': 'episode'}],
                     'paging': {'page': 1, 'total': 1}},
    }
    card_calls = []

    def get_programcard(path, **k):
        card_calls.append(k.get('use_cache'))
        return {'item': season}

    unfold_calls = []
    monkeypatch.setattr(handle.api, 'get_programcard', get_programcard)
    monkeypatch.setattr(handle.api, 'unfold_list',
                        lambda item, **k: unfold_calls.append(k.get('use_cache')) or [])
    monkeypatch.setattr(handle, 'listEpisodes', lambda items, **k: None)

    handle.list_entries('/serie/bluey_227278', caching=False)

    assert card_calls == [False]
    assert unfold_calls == [False]


def test_list_entries_threads_no_caching_to_a_list_page(handle, monkeypatch):
    """A list page carries its items at top level; the unfold must stay
    uncached too."""
    page = {'list': {'items': [], 'paging': {}}}
    monkeypatch.setattr(handle.api, 'get_programcard', lambda path, **k: page)
    unfold_calls = []
    monkeypatch.setattr(handle.api, 'unfold_list',
                        lambda item, **k: unfold_calls.append(k.get('use_cache')) or [])
    monkeypatch.setattr(handle, 'listEpisodes', lambda items, **k: None)

    handle.list_entries('/liste/nye-programmer-xf0na', caching=False)

    assert unfold_calls == [False]


def test_list_entries_lists_a_list_page(handle, monkeypatch):
    """A /liste/ page exposes the whole list at top level; the entries are
    CustomEntry/ListDetailEntry stubs and must be ignored."""
    page = {'list': {'items': [{'id': 'a', 'type': 'show'}], 'paging': {}},
            'entries': [{'type': 'CustomEntry'}, {'type': 'ListDetailEntry'}]}
    monkeypatch.setattr(handle.api, 'get_programcard', lambda path, **k: page)
    monkeypatch.setattr(handle.api, 'unfold_list', lambda item, **k: item['items'])
    listed = []
    monkeypatch.setattr(handle, 'listEpisodes', lambda items, **k: listed.append(items))

    handle.list_entries('/liste/nye-programmer-xf0na')

    assert listed == [[{'id': 'a', 'type': 'show'}]]


def _unfold_api(pages):
    """An Api whose get_next serves the given pages in order and records calls."""
    from resources.lib import tvapi
    api = tvapi.Api.__new__(tvapi.Api)
    api.kids_item = lambda item: False
    api.calls = []

    def get_next(path, use_cache=True, headers=None):
        api.calls.append({'path': path, 'headers': headers, 'use_cache': use_cache})
        return pages.pop(0)

    api.get_next = get_next
    return api


def test_unfold_list_ignores_empty_next():
    """DR's /search sends paging.next as an empty string, not a missing key.

    Requesting that empty path hit the bare API root and raised on its HTML
    404, so every search result crashed before showing anything (issue 136).
    """
    api = _unfold_api([])
    section = {'items': [{'id': 1}], 'paging': {'page': 1, 'total': 2, 'next': ''}}

    assert api.unfold_list(section) == [{'id': 1}]
    assert api.calls == []


def test_unfold_list_follows_real_next_until_exhausted():
    api = _unfold_api([
        {'items': [{'id': 2}], 'paging': {'page': 2, 'total': 3, 'next': '/next?page=3'}},
        {'items': [{'id': 3}], 'paging': {'page': 3, 'total': 3, 'next': ''}},
    ])
    section = {'items': [{'id': 1}], 'paging': {'page': 1, 'total': 3, 'next': '/next?page=2'}}

    assert api.unfold_list(section) == [{'id': 1}, {'id': 2}, {'id': 3}]
    assert [c['path'] for c in api.calls] == ['/next?page=2', '/next?page=3']


def test_searchresult_pages_need_no_header(handle, monkeypatch, tmp_path):
    """The catalog endpoints (search included) need no token on the new API,
    so the later pages are requested without one — sending a token there was
    only ever needed because the legacy search was authorized."""
    import pickle
    search_path = tmp_path / 'search6.pickle'
    section = {'items': [{'id': 1, 'type': 'episode'}],
               'paging': {'page': 1, 'total': 2, 'next': '/next?page=2'}}
    with search_path.open('wb') as fh:
        pickle.dump({'series': section}, fh)
    handle.search_path = search_path

    unfold_calls = []
    monkeypatch.setattr(handle.api, 'unfold_list',
                        lambda item, **k: unfold_calls.append(k.get('headers')) or [])
    monkeypatch.setattr(handle, 'listEpisodes', lambda items, **k: None)

    handle.route('?searchresult=series')

    assert unfold_calls == [None]

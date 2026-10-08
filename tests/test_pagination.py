"""Tests for pagination in list_entries and search results.

Listings used to stop at the first page (page size 24), hiding later videos.
Both paths must follow the remaining pages via unfold_list, which the other
listing branches already did.
"""


def test_list_entries_unfolds_episode_pages(handle, monkeypatch):
    """The single-season branch must expand the episode list, not slice its
    first page."""
    season = {
        'type': 'ItemEntry',
        'item': {
            'type': 'season',
            'show': {'availableSeasonCount': 1},
            'episodes': {'items': [{'id': 1, 'type': 'episode'}],
                         'paging': {'page': 1, 'total': 1}},
        },
    }
    monkeypatch.setattr(handle.api, 'get_programcard', lambda path, **k: {'entries': [season]})
    unfolded = []
    monkeypatch.setattr(handle.api, 'unfold_list',
                        lambda item, **k: unfolded.append(item) or [{'id': 1, 'type': 'episode'}])
    listed = []
    monkeypatch.setattr(handle, 'listEpisodes', lambda items, **k: listed.append(items))

    handle.list_entries('/serie/bluey_227278')

    assert unfolded == [season['item']['episodes']]
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

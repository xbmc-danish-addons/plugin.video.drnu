"""Tests for the playable/folder classification in gui.kodi_item.

Movies are playable videos like programs and episodes; treating them as
folders sent them to list_entries, which rejects non-season ItemEntry items.
"""
from resources.lib import gui


class FakeApi:
    def __init__(self):
        self.args = {}

    def get_title(self, item):
        return item['title']

    def set_info(self, item, tag, title):
        pass

    def item_area(self, item):
        return 'drtv'

    def kids_item(self, item):
        return False


def _item(item_type, **extra):
    item = {'id': 1, 'title': 'A title', 'type': item_type, 'path': f'/x/{item_type}'}
    item.update(extra)
    return item


def test_movie_is_playable():
    result = gui.kodi_item('plugin://plugin.video.drnu/', FakeApi(), [], 'fanart.jpg', _item('movie'))
    assert result is not None
    url, _listitem, is_folder = result
    assert is_folder is False
    assert '?playVideo=' in url


def test_program_and_episode_are_playable():
    for item_type in ('program', 'episode'):
        _url, _listitem, is_folder = gui.kodi_item(
            'plugin://plugin.video.drnu/', FakeApi(), [], 'fanart.jpg', _item(item_type))
        assert is_folder is False


def test_season_is_a_folder():
    _url, _listitem, is_folder = gui.kodi_item(
        'plugin://plugin.video.drnu/', FakeApi(), [], 'fanart.jpg', _item('season'))
    assert is_folder is True

"""Tests for the playable/folder classification and image selection in
gui.kodi_item.

Movies are playable videos like programs and episodes; treating them as
folders sent them to list_entries, which rejects non-season ItemEntry items.

Fanart must be the 16:9 background (DR's 'wallpaper'/'tile'), not the 2:3
'poster': a missing break in the label loop let a later label overwrite an
earlier one, so poster won and the background came out too tall.
"""
from resources.lib import gui
from resources.lib.kodiutils import set_setting


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


def _fanart(item):
    _url, listitem, _folder = gui.kodi_item(
        'plugin://plugin.video.drnu/', FakeApi(), [], 'default-fanart.jpg', item)
    return listitem.art['fanart']


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


def test_fanart_prefers_wallpaper_over_poster():
    item = _item('episode', images={'wallpaper': 'wp.jpg', 'tile': 'tile.jpg', 'poster': 'poster.jpg'})
    assert _fanart(item) == 'wp.jpg'


def test_fanart_falls_back_to_tile_without_wallpaper():
    item = _item('episode', images={'tile': 'tile.jpg', 'poster': 'poster.jpg'})
    assert _fanart(item) == 'tile.jpg'


def test_fanart_uses_poster_only_as_last_resort():
    item = _item('episode', images={'poster': 'poster.jpg'})
    assert _fanart(item) == 'poster.jpg'


def test_fanart_falls_back_to_default_without_images():
    item = _item('episode')
    item.pop('images', None)
    assert _fanart(item) == 'default-fanart.jpg'


def test_duration_suffix_formats_hours_and_minutes():
    assert gui.duration_suffix(3569) == ' [0:59]'
    assert gui.duration_suffix(3570) == ' [1:00]'  # 59.5 min rounds up
    assert gui.duration_suffix(3690) == ' [1:02]'  # 3690s rounds to 62 min
    assert gui.duration_suffix(7200) == ' [2:00]'
    assert gui.duration_suffix(5400) == ' [1:30]'
    assert gui.duration_suffix(0) == ' [0:00]'


def test_duration_suffix_ignores_non_numeric():
    assert gui.duration_suffix(None) == ''
    assert gui.duration_suffix('') == ''
    assert gui.duration_suffix('42') == ''


def test_duration_setting_off_leaves_label_unchanged():
    _url, listitem, _folder = gui.kodi_item(
        'plugin://plugin.video.drnu/', FakeApi(), [], 'fanart.jpg', _item('episode', duration=3600))
    assert listitem.label == 'A title'


def test_duration_setting_on_appends_suffix_to_playables():
    set_setting('video.duration', 'true')
    try:
        _url, listitem, _folder = gui.kodi_item(
            'plugin://plugin.video.drnu/', FakeApi(), [], 'fanart.jpg', _item('episode', duration=5400))
        assert listitem.label == 'A title [1:30]'
    finally:
        set_setting('video.duration', 'false')


def test_duration_setting_on_skips_folders_and_missing_duration():
    set_setting('video.duration', 'true')
    try:
        _url, listitem, _folder = gui.kodi_item(
            'plugin://plugin.video.drnu/', FakeApi(), [], 'fanart.jpg', _item('season', duration=3600))
        assert listitem.label == 'A title'

        _url, listitem, _folder = gui.kodi_item(
            'plugin://plugin.video.drnu/', FakeApi(), [], 'fanart.jpg', _item('episode'))
        assert listitem.label == 'A title'
    finally:
        set_setting('video.duration', 'false')


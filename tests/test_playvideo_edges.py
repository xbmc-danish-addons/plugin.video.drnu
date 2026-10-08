"""Regression tests for addon.playVideo and list route edge cases.

Covers the review findings: an unavailable stream, the live-TV subtitle
setting, and the menu fanart path.
"""
from resources.lib import addon as addon_module


def test_playvideo_handles_missing_stream(handle, monkeypatch):
    """get_stream() returns None when no StandardVideo stream exists; playback
    must report failure with the unavailable-video message, not crash."""
    errors = []
    resolved = []
    monkeypatch.setattr(handle.api, 'get_stream', lambda video_id: None)
    monkeypatch.setattr(handle, 'displayError', lambda message='': errors.append(message))
    monkeypatch.setattr(addon_module.xbmcplugin, 'setResolvedUrl',
                        lambda h, succeeded, item: resolved.append(succeeded))

    handle.playVideo(1234, 'False', '/program/abc')

    assert errors == [addon_module.tr(30904)]
    assert resolved == [False]


def test_playvideo_live_uses_livetv_subtitle_setting(handle, monkeypatch):
    """The /kanal branch must honor enable.livetv_subtitles, matching the
    direct live-TV page."""
    captured = {}
    monkeypatch.setattr(addon_module, 'bool_setting', lambda name: name == 'enable.livetv_subtitles')
    monkeypatch.setattr(addon_module, 'get_setting', lambda name: '1')

    def get_livestream(path, with_subtitles=False):
        captured['path'] = path
        captured['with_subtitles'] = with_subtitles
        return {'url': 'https://example.com/live.m3u8', 'subtitles': []}

    monkeypatch.setattr(handle.api, 'get_livestream', get_livestream)
    monkeypatch.setattr(addon_module.xbmcplugin, 'setResolvedUrl', lambda *a: None)

    handle.playVideo('x', 'False', '/kanal/dr1')

    assert captured['path'] == '/kanal/dr1'
    assert captured['with_subtitles'] is True


def test_fanart_image_is_under_media(handle):
    """The packaged image lives in resources/media/, not resources/."""
    assert handle.fanart_image.endswith('resources/media/fanart.jpg')


def test_route_listvideos_empty_list_shows_empty_directory(handle, monkeypatch):
    """An empty list (and empty recommendations) must yield an empty page,
    not an IndexError on items[0]."""
    monkeypatch.setattr(handle.api, 'get_list', lambda *a, **k: {'items': []})
    listed = []
    monkeypatch.setattr(handle, 'listEpisodes', lambda items, **k: listed.append(items))

    handle.route('?listVideos=ID_306104&list_param=NoParam')

    assert listed == [[]]


def _resolved_item_for(handle, monkeypatch, has_adaptive):
    video = {'url': 'https://example.com/v.m3u8', 'subtitles': [], 'srt_subtitles': []}
    monkeypatch.setattr(handle.api, 'get_stream', lambda video_id: video)
    monkeypatch.setattr(addon_module, 'bool_setting', lambda name: False)
    monkeypatch.setattr(addon_module, 'get_setting', lambda name: '0')
    monkeypatch.setattr(addon_module.xbmc, 'getCondVisibility', lambda cond: has_adaptive)
    resolved = []
    monkeypatch.setattr(addon_module.xbmcplugin, 'setResolvedUrl',
                        lambda h, ok, item: resolved.append(item))
    handle.playVideo(1234, 'False', '/program/abc')
    return resolved[0]


def test_playvideo_forces_adaptive_when_installed(handle, monkeypatch):
    item = _resolved_item_for(handle, monkeypatch, has_adaptive=True)
    assert item.properties.get('inputstream') == 'inputstream.adaptive'


def test_playvideo_falls_back_without_adaptive(handle, monkeypatch):
    """inputstream.adaptive is optional; when it is not installed, forcing the
    property would break playback, so Kodi's built-in player must handle it."""
    item = _resolved_item_for(handle, monkeypatch, has_adaptive=False)
    assert 'inputstream' not in item.properties

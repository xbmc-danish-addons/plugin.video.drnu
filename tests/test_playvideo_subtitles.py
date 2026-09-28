"""Regression tests for playVideo subtitle handling on the resolved player.

Covers the Kodi crash fixed after 7.0.0: Player.setSubtitles() takes a single
path string, not a list (ListItem.setSubtitles() is the list-taking variant).
"""
import xbmc

from resources.lib import addon as addon_module


class FakePlayer(xbmc.Player):
    """Records setSubtitles/setSubtitleStream/showSubtitles calls."""

    instances = []

    def __init__(self):
        super().__init__()
        self.calls = []
        FakePlayer.instances.append(self)

    def isPlaying(self):
        return True

    def setSubtitles(self, subtitleFile):
        super().setSubtitles(subtitleFile)
        self.calls.append(('setSubtitles', subtitleFile))

    def setSubtitleStream(self, url):
        super().setSubtitleStream(url)
        self.calls.append(('setSubtitleStream', url))

    def showSubtitles(self, bVisible):
        self.calls.append(('showSubtitles', bVisible))


class FakeMonitor:
    """Immediately reports playback started."""

    @staticmethod
    def waitForAbort(timeout):
        return False


def test_playvideo_local_subtitles_passes_single_path(handle, monkeypatch):
    """action == 'local' must hand Player.setSubtitles() one path string."""
    FakePlayer.instances = []
    video = {
        'url': 'https://example.com/video.m3u8',
        'subtitles': [{'language': 'DanishLanguageSubtitles'}],
        'srt_subtitles': ['/tmp/a.srt', '/tmp/b.srt'],
    }
    monkeypatch.setattr(handle.api, 'get_stream', lambda video_id: video)
    monkeypatch.setattr(addon_module, 'bool_setting', lambda name: True)
    monkeypatch.setattr(addon_module, 'get_setting', lambda name: 1)
    monkeypatch.setattr(addon_module.xbmc, 'Player', FakePlayer)
    monkeypatch.setattr(addon_module.xbmc, 'Monitor', FakeMonitor)

    handle.playVideo(1234, 'False', '/program/abc')

    assert len(FakePlayer.instances) == 1
    player = FakePlayer.instances[0]
    assert player.calls == [('setSubtitles', '/tmp/b.srt'), ('showSubtitles', True)]


def test_playvideo_stream_subtitles_use_stream_index(handle, monkeypatch):
    """Without local SRT files the embedded stream index is used."""
    FakePlayer.instances = []
    video = {
        'url': 'https://example.com/video.m3u8',
        'subtitles': [{'language': 'ForeignLanguageSubtitles'}],
        'srt_subtitles': [],
    }
    monkeypatch.setattr(handle.api, 'get_stream', lambda video_id: video)
    monkeypatch.setattr(addon_module, 'bool_setting', lambda name: False)
    monkeypatch.setattr(addon_module, 'get_setting', lambda name: 0)
    monkeypatch.setattr(addon_module.xbmc, 'Player', FakePlayer)
    monkeypatch.setattr(addon_module.xbmc, 'Monitor', FakeMonitor)

    handle.playVideo(1234, 'False', '/program/abc')

    player = FakePlayer.instances[0]
    assert player.calls == [('setSubtitleStream', 0), ('showSubtitles', True)]

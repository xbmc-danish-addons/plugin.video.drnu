"""Unit tests for the playVideo wait loop (Monitor-based, abortable)."""
from resources.lib import addon as addon_module


def test_wait_for_playback_returns_on_first_playing(monkeypatch):
    calls = []

    class FakePlayer:
        @staticmethod
        def isPlaying():
            calls.append('isPlaying')
            return True

    class FakeMonitor:
        @staticmethod
        def waitForAbort(timeout):
            calls.append(('waitForAbort', timeout))
            return False

    monkeypatch.setattr(addon_module.xbmc, 'Player', FakePlayer)
    monkeypatch.setattr(addon_module.xbmc, 'Monitor', FakeMonitor)
    addon_module._wait_for_playback(FakePlayer(), FakeMonitor())
    assert calls == ['isPlaying', ('waitForAbort', 1.0)]


def test_wait_for_playback_gives_up_after_timeout(monkeypatch):
    calls = []

    class FakePlayer:
        @staticmethod
        def isPlaying():
            return False

    class FakeMonitor:
        @staticmethod
        def waitForAbort(timeout):
            calls.append(timeout)
            return False

    monkeypatch.setattr(addon_module.xbmc, 'Player', FakePlayer)
    monkeypatch.setattr(addon_module.xbmc, 'Monitor', FakeMonitor)
    addon_module._wait_for_playback(FakePlayer(), FakeMonitor())
    # 25 x 0.2s = 5s of waiting, then give up without the settle wait
    assert len(calls) == 25
    assert calls[-1] == 0.2


def test_wait_for_playback_aborts_on_kodi_shutdown(monkeypatch):
    calls = []

    class FakePlayer:
        @staticmethod
        def isPlaying():
            return False

    class FakeMonitor:
        @staticmethod
        def waitForAbort(timeout):
            calls.append(timeout)
            return True  # abortRequested

    monkeypatch.setattr(addon_module.xbmc, 'Player', FakePlayer)
    monkeypatch.setattr(addon_module.xbmc, 'Monitor', FakeMonitor)
    addon_module._wait_for_playback(FakePlayer(), FakeMonitor())
    assert calls == [0.2]  # single abort check, then bail

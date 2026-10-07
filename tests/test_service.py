"""Unit tests for the service.py entry point loop and its playback guard."""
import service as service_module


class FakeMonitor:
    def __init__(self, aborts):
        self.aborts = list(aborts)
        self.waits = []

    def abortRequested(self):
        return self.aborts.pop(0)

    def waitForAbort(self, timeout):
        self.waits.append(timeout)
        return False


def test_run_loop_cleans_until_abort():
    calls = []
    mon = FakeMonitor([False, True])
    service_module.run(mon, lambda: calls.append(1), 0)
    assert calls == [1]
    assert mon.waits == [0]


def test_run_loop_survives_cleanup_exception():
    calls = []

    def bad():
        calls.append(1)
        raise RuntimeError('boom')

    mon = FakeMonitor([False, False, True])
    service_module.run(mon, bad, 0)
    assert len(calls) == 2


def test_cleanup_once_skipped_while_playing(monkeypatch, tmp_path):
    import xbmc
    monkeypatch.setattr(xbmc, 'getCondVisibility', lambda s: True)
    seen = []
    monkeypatch.setattr(service_module, 'run_cleanup', lambda *a, **k: seen.append(a))
    service_module.cleanup_once(tmp_path)
    assert seen == []


def test_cleanup_once_calls_run_cleanup(monkeypatch, tmp_path):
    import xbmc
    monkeypatch.setattr(xbmc, 'getCondVisibility', lambda s: False)
    seen = []
    monkeypatch.setattr(service_module, 'run_cleanup',
                        lambda get_setting, cache_path, log_func: seen.append(cache_path) or True)
    service_module.cleanup_once(tmp_path)
    assert seen == [tmp_path]


def test_idle_and_not_playing(monkeypatch):
    import xbmc
    monkeypatch.setattr(xbmc, 'getCondVisibility', lambda s: s != 'Player.playing')
    monkeypatch.setattr(xbmc, 'getGlobalIdleTime', lambda: 400)
    assert service_module.idle_and_not_playing() is True
    monkeypatch.setattr(xbmc, 'getGlobalIdleTime', lambda: 10)
    assert service_module.idle_and_not_playing() is False
    monkeypatch.setattr(xbmc, 'getCondVisibility', lambda s: True)
    assert service_module.idle_and_not_playing() is False


def test_recache_once_wires_pass(monkeypatch, tmp_path):
    seen = {}

    def fake_pass(get_setting, api_factory, cache_path, now, idle_check, dialog_factory, log_func=None):
        seen['cache_path'] = cache_path
        seen['dialog_factory'] = dialog_factory
        seen['now'] = now
        seen['log_func'] = log_func
        return True

    monkeypatch.setattr(service_module, 'recache_pass', fake_pass)
    monkeypatch.setattr(service_module, 'log', lambda *a, **k: seen.setdefault('logged', True))
    service_module.recache_once(tmp_path)
    assert seen['cache_path'] == tmp_path
    assert seen['dialog_factory'] is service_module.make_bg_dialog
    # log_func is the INFO-level wrapper, not raw log()
    assert seen['log_func'] is service_module._log_info
    assert 'logged' in seen


def test_make_bg_dialog_creates_dialog(monkeypatch):
    created = {}

    class FakeDialog:
        def create(self, heading, message):
            created['heading'] = heading
            created['message'] = message

    monkeypatch.setattr(service_module.xbmcgui, 'DialogProgressBG', FakeDialog)
    monkeypatch.setattr(service_module, 'tr', lambda i: 'localized')
    dialog = service_module.make_bg_dialog()
    assert isinstance(dialog, FakeDialog)
    assert created['heading'] == 'DR TV'
    assert created['message'] == 'localized'


def test_make_bg_dialog_degrades_without_gui(monkeypatch):
    class RaisingDialog:
        def create(self, heading, message):
            raise RuntimeError('Dialog not created.')

    monkeypatch.setattr(service_module.xbmcgui, 'DialogProgressBG', RaisingDialog)
    monkeypatch.setattr(service_module, 'tr', lambda i: 'localized')
    assert service_module.make_bg_dialog() is None


def test_make_bg_dialog_closes_dialog_that_failed_create(monkeypatch):
    """create() can raise after Kodi registered the handle (e.g. the service
    starts before the GUI is up); that handle must not be left at 0%."""
    closed = []

    class RaisingDialog:
        def create(self, heading, message):
            raise RuntimeError('Dialog not created.')

        def close(self):
            closed.append(True)

    monkeypatch.setattr(service_module.xbmcgui, 'DialogProgressBG', RaisingDialog)
    monkeypatch.setattr(service_module, 'tr', lambda i: 'localized')
    assert service_module.make_bg_dialog() is None
    assert closed == [True]


def test_recache_once_silent_when_not_due(monkeypatch, tmp_path):
    monkeypatch.setattr(service_module, 'recache_pass', lambda *a, **k: False)
    logged = []
    monkeypatch.setattr(service_module, 'log', lambda *a, **k: logged.append(a))
    service_module.recache_once(tmp_path)
    assert logged == []

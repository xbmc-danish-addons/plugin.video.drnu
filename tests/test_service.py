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

    def fake_pass(get_setting, api_factory, cache_path, now, idle_check, dialog_factory,
                  log_func=None, shutdown_check=None):
        seen['cache_path'] = cache_path
        seen['dialog_factory'] = dialog_factory
        seen['now'] = now
        seen['log_func'] = log_func
        seen['shutdown_check'] = shutdown_check
        return True

    monkeypatch.setattr(service_module, 'recache_pass', fake_pass)
    monkeypatch.setattr(service_module, '_log', lambda *a, **k: seen.setdefault('logged', True))
    shutdown = lambda: False
    service_module.recache_once(tmp_path, shutdown)
    assert seen['cache_path'] == tmp_path
    assert seen['dialog_factory'] is service_module.make_bg_dialog
    # log_func is the INFO-level logger that bypasses the log.debug gate
    assert seen['log_func'] is service_module._log
    # the shutdown check is threaded through to the crawl
    assert seen['shutdown_check'] is shutdown
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
    monkeypatch.setattr(service_module, '_log', lambda *a, **k: logged.append(a))
    service_module.recache_once(tmp_path, lambda: False)
    assert logged == []


def test_main_creates_profile_dir(monkeypatch, tmp_path):
    """A fresh install has no profile dir; main() must create it before the
    first pass writes recache.state, or every pass raises FileNotFoundError."""
    profile = tmp_path / 'profile'
    assert not profile.exists()

    class FakeAddon:
        def getAddonInfo(self, key):
            return str(profile)

    class FakeMonitor:
        def abortRequested(self):
            return True

    monkeypatch.setattr(service_module.xbmcaddon, 'Addon', FakeAddon)
    monkeypatch.setattr(service_module.xbmc, 'Monitor', FakeMonitor)
    service_module.main()
    assert profile.is_dir()


def test_run_wires_monitor_shutdown_into_recache(monkeypatch):
    """run() must hand the crawl the monitor's abortRequested, so exiting Kodi
    stops a running re-cache."""
    seen = {}

    def fake_recache(cache_path, shutdown_check):
        seen['shutdown_check'] = shutdown_check

    class Monitor:
        def __init__(self):
            self.aborted = False

        def abortRequested(self):
            return self.aborted

        def waitForAbort(self, timeout):
            self.aborted = True  # end the loop after the first pass
            return True

    monkeypatch.setattr(service_module, 'cleanup_once', lambda cache_path: None)
    monkeypatch.setattr(service_module, 'recache_once', fake_recache)
    monitor = Monitor()
    service_module.run(monitor, lambda: (service_module.cleanup_once('x'),
                                         service_module.recache_once('x', monitor.abortRequested)), 0)
    # the crawl's check reflects the monitor state, so it aborts on exit
    assert seen['shutdown_check']() is True

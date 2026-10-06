"""Unit tests for resources/lib/recachescheduler.py (no Kodi needed)."""
from datetime import datetime, time
from typing import Dict, List, Optional

from resources.lib import recachescheduler
from resources.lib.recachescheduler import (IdleAbortProgress, RecacheState,
                                            due_slot, parse_time_setting,
                                            recache_due, recache_pass)

NOW = datetime(2026, 10, 3, 3, 5)
AT = time(3, 0)


def test_state_roundtrip(tmp_path):
    state = RecacheState(tmp_path)
    assert state.load() is None
    slot = datetime(2026, 10, 3, 3, 0)
    state.save(slot)
    assert RecacheState(tmp_path).load() == slot


def test_state_corrupt_file_is_ignored(tmp_path):
    (tmp_path / recachescheduler.STATE_FILE).write_text('not a date')
    assert RecacheState(tmp_path).load() is None


def test_recache_due_seeds_first_run(tmp_path):
    state = RecacheState(tmp_path)
    assert recache_due(state, AT, NOW) is None
    # seeded: state file now exists with 'now'
    assert RecacheState(tmp_path).load() == NOW


def test_recache_due_fires_on_slot(tmp_path):
    state = RecacheState(tmp_path)
    state.save(datetime(2026, 10, 2, 12, 0))
    assert recache_due(state, AT, NOW) == datetime(2026, 10, 3, 3, 0)


def test_recache_due_not_yet(tmp_path):
    state = RecacheState(tmp_path)
    state.save(NOW)
    assert recache_due(state, AT, NOW) is None


def test_parse_time_setting():
    assert parse_time_setting('03:00') == time(3, 0)
    assert parse_time_setting('3:00') == time(3, 0)
    assert parse_time_setting('23:59') == time(23, 59)
    assert parse_time_setting('0:15') == time(0, 15)
    assert parse_time_setting('03:00:00') == time(3, 0)
    assert parse_time_setting(' 03:00 ') == time(3, 0)
    assert parse_time_setting('') is None
    assert parse_time_setting('xx') is None
    assert parse_time_setting('24:00') is None
    assert parse_time_setting('03:60') is None
    assert parse_time_setting('3') is None


def test_due_slot():
    assert due_slot(datetime(2026, 10, 2, 12, 0), NOW, AT) == datetime(2026, 10, 3, 3, 0)
    # slot exactly at last is not re-reported
    assert due_slot(datetime(2026, 10, 3, 3, 0), NOW, AT) is None
    # 3:30 schedule, last acted on yesterday 3:00: today's 3:30 not reached,
    # so yesterday's 3:30 is the most recent unacted slot
    assert due_slot(datetime(2026, 10, 2, 3, 0), NOW, time(3, 30)) == datetime(2026, 10, 2, 3, 30)
    # before today's slot: yesterday's is due
    early = datetime(2026, 10, 3, 2, 59)
    assert due_slot(datetime(2026, 10, 2, 3, 0), early, AT) is None
    # midnight wrap: 00:05 with 00:00 schedule
    now2 = datetime(2026, 10, 3, 0, 5)
    assert due_slot(datetime(2026, 10, 2, 12, 0), now2, time(0, 0)) == datetime(2026, 10, 3, 0, 0)
    # last=None: the most recent slot <= now (recache_due seeds before
    # calling due_slot, so this only matters for direct callers)
    assert due_slot(None, NOW, AT) == datetime(2026, 10, 3, 3, 0)
    assert due_slot(None, early, AT) == datetime(2026, 10, 2, 3, 0)


class FakeDialog:
    def __init__(self):
        self.updates: List[tuple] = []
        self.closed = False

    def update(self, percentage, heading=None, message=None):
        self.updates.append((percentage, message))

    def close(self):
        self.closed = True


class FakeApi:
    def __init__(self):
        self.calls: List[dict] = []

    def recache_items(self, progress=None, clear_expired=False):
        self.calls.append({'progress': progress, 'clear_expired': clear_expired})
        progress.update(10, 'working')
        assert not progress.iscanceled()
        progress.update(50, 'still working')


def _settings(overrides: Optional[Dict[str, str]] = None):
    s = {'recache.enabled': 'true', 'recache.service': 'true',
         'recache.service.idle': 'true', 'recache.time': '03:00'}
    if overrides:
        s.update(overrides)
    return s.get


def _run_pass(tmp_path, settings, idle=True, api=None, last=None):
    """Run one recache_pass with fakes; returns (result, api, progress_seen)."""
    api = api or FakeApi()
    if last is not None:
        RecacheState(tmp_path).save(last)
    progress_seen = []

    def progress_factory(dialog, idle_check):
        p = IdleAbortProgress(dialog, idle_check)
        progress_seen.append(p)
        return p

    result = recache_pass(settings, lambda: api, tmp_path, NOW,
                          lambda: idle, FakeDialog, progress_factory)
    return result, api, (progress_seen[0] if progress_seen else None)


def test_pass_runs_when_due_and_idle(tmp_path):
    last = datetime(2026, 10, 2, 12, 0)
    result, api, progress = _run_pass(tmp_path, _settings(), idle=True, last=last)
    assert result is True
    assert len(api.calls) == 1
    assert api.calls[0]['clear_expired'] is True
    assert progress.idle_check() is True
    # slot marked done
    assert RecacheState(tmp_path).load() == datetime(2026, 10, 3, 3, 0)


def test_pass_blocked_by_idle_gate(tmp_path):
    last = datetime(2026, 10, 2, 12, 0)
    result, api, progress = _run_pass(tmp_path, _settings(), idle=False, last=last)
    assert result is False
    assert api.calls == []
    # slot NOT marked done — retried on a later idle pass
    assert RecacheState(tmp_path).load() == last


def test_pass_idle_gate_disabled_setting(tmp_path):
    last = datetime(2026, 10, 2, 12, 0)
    result, api, _ = _run_pass(tmp_path, _settings({'recache.service.idle': 'false'}),
                               idle=False, last=last)
    assert result is True
    assert len(api.calls) == 1


def test_pass_not_due(tmp_path):
    result, api, _ = _run_pass(tmp_path, _settings(), idle=True, last=NOW)
    assert result is False
    assert api.calls == []


def test_pass_disabled_settings(tmp_path):
    for key in ['recache.enabled', 'recache.service']:
        result, api, _ = _run_pass(tmp_path, _settings({key: 'false'}), idle=True,
                                   last=datetime(2026, 10, 2, 12, 0))
        assert result is False
        assert api.calls == []


def test_pass_invalid_time_setting(tmp_path):
    result, api, _ = _run_pass(tmp_path, _settings({'recache.time': 'xx'}), idle=True,
                               last=datetime(2026, 10, 2, 12, 0))
    assert result is False
    assert api.calls == []


def test_pass_aborts_when_user_becomes_active(tmp_path):
    class AbortingApi(FakeApi):
        def recache_items(self, progress=None, clear_expired=False):
            self.calls.append({'progress': progress, 'clear_expired': clear_expired})
            progress.update(10, 'working')
            # user comes back mid-crawl
            progress.idle_check = lambda: False
            assert progress.iscanceled() is True
            return  # recache_items returns early on iscanceled

    last = datetime(2026, 10, 2, 12, 0)
    result, api, progress = _run_pass(tmp_path, _settings(), idle=True, api=AbortingApi(), last=last)
    assert result is False
    assert progress.was_aborted is True
    # slot left unsaved so the job retries on the next idle pass
    assert RecacheState(tmp_path).load() == last


def test_idle_abort_progress_latches_abort():
    p = IdleAbortProgress(FakeDialog(), lambda: False)
    assert p.iscanceled() is True
    # stays aborted even if idle_check flips back
    p.idle_check = lambda: True
    assert p.iscanceled() is True


def test_idle_abort_progress_forwards_updates():
    dialog = FakeDialog()
    p = IdleAbortProgress(dialog, lambda: True)
    p.update(42.6, 'msg')
    assert dialog.updates == [(42, 'msg')]


def _pass_with_dialog(tmp_path, factory=None, api=None, last=None):
    """Run recache_pass with a dialog we keep a reference to.

    Returns (result, dialog, raised). 'factory' builds the dialog
    (FakeDialog by default); 'api' is called after the dialog exists.
    """
    if last is not None:
        RecacheState(tmp_path).save(last)
    dialog = FakeDialog()
    api = api or FakeApi()
    settings = _settings({'recache.service.idle': 'true'})
    raised = None
    try:
        result = recache_pass(settings, lambda: api, tmp_path, NOW,
                              lambda: True, factory or (lambda: dialog))
    except Exception as exc:  # the pass is expected to close before re-raising
        result, raised = None, exc
    return result, dialog, raised


def test_pass_closes_dialog_on_success(tmp_path):
    result, dialog, raised = _pass_with_dialog(tmp_path, last=datetime(2026, 10, 2, 12, 0))
    assert result is True
    assert raised is None
    assert dialog.closed is True


def test_pass_closes_dialog_when_crawl_raises(tmp_path):
    class BoomApi(FakeApi):
        def recache_items(self, progress=None, clear_expired=False):
            raise RuntimeError('network died')

    _, dialog, raised = _pass_with_dialog(tmp_path, api=BoomApi(),
                                          last=datetime(2026, 10, 2, 12, 0))
    assert isinstance(raised, RuntimeError)
    assert dialog.closed is True
    # slot not marked done, so the crawl retries on the next idle pass
    assert RecacheState(tmp_path).load() == datetime(2026, 10, 2, 12, 0)


def test_pass_propagates_factory_error(tmp_path):
    def factory():
        raise RuntimeError('Dialog not created.')

    result, _, raised = _pass_with_dialog(tmp_path, factory=factory,
                                          last=datetime(2026, 10, 2, 12, 0))
    assert result is None
    assert isinstance(raised, RuntimeError)
    # the crawl never ran, so the slot stays open for the next pass
    assert RecacheState(tmp_path).load() == datetime(2026, 10, 2, 12, 0)


def test_pass_close_failure_does_not_mask_result(tmp_path):
    class StubbornDialog(FakeDialog):
        def close(self):
            raise RuntimeError('Dialog not created.')

    result, _, raised = _pass_with_dialog(tmp_path, factory=StubbornDialog,
                                          last=datetime(2026, 10, 2, 12, 0))
    assert raised is None
    assert result is True


def test_close_dialog_tolerates_none_and_errors():
    recachescheduler._close_dialog(None)

    class Stubborn(FakeDialog):
        def close(self):
            raise RuntimeError('nope')

    recachescheduler._close_dialog(Stubborn())


def test_pass_closes_dialog_when_aborted(tmp_path):
    class AbortingApi(FakeApi):
        def recache_items(self, progress=None, clear_expired=False):
            self.calls.append({'progress': progress, 'clear_expired': clear_expired})
            progress.idle_check = lambda: False
            progress.iscanceled()

    _, dialog, raised = _pass_with_dialog(tmp_path, api=AbortingApi(),
                                          last=datetime(2026, 10, 2, 12, 0))
    assert raised is None
    assert dialog.closed is True

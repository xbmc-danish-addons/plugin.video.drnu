"""Unit tests for resources/lib/recachescheduler.py (no Kodi needed)."""
from datetime import datetime
from typing import Dict, List, Optional

import pytest

from resources.lib import recachescheduler
from resources.lib.recachescheduler import (IdleAbortProgress, RecacheState,
                                            recache_due, recache_pass)

NOW = datetime(2026, 9, 29, 3, 5)


def test_state_roundtrip(tmp_path):
    state = RecacheState(tmp_path)
    assert state.load() is None
    slot = datetime(2026, 9, 29, 3, 0)
    state.save(slot)
    assert RecacheState(tmp_path).load() == slot


def test_state_corrupt_file_is_ignored(tmp_path):
    (tmp_path / recachescheduler.STATE_FILE).write_text('not a date')
    assert RecacheState(tmp_path).load() is None


def test_recache_due_seeds_first_run(tmp_path):
    state = RecacheState(tmp_path)
    assert recache_due(state, '0 3 * * *', NOW) is None
    # seeded: state file now exists with 'now'
    assert RecacheState(tmp_path).load() == NOW


def test_recache_due_fires_on_slot(tmp_path):
    state = RecacheState(tmp_path)
    state.save(datetime(2026, 9, 28, 12, 0))
    assert recache_due(state, '0 3 * * *', NOW) == datetime(2026, 9, 29, 3, 0)


def test_recache_due_not_yet(tmp_path):
    state = RecacheState(tmp_path)
    state.save(NOW)
    assert recache_due(state, '0 3 * * *', NOW) is None


class FakeDialog:
    def __init__(self):
        self.updates: List[tuple] = []
        self.created = False
        self.closed = False

    def create(self, heading, message):
        self.created = True

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
         'recache.service.idle': 'true', 'recache.cronexpression': '0 3 * * *'}
    if overrides:
        s.update(overrides)
    return s.get


_USE_DEFAULT_DIALOG = object()


def _run_pass(tmp_path, settings, idle=True, api=None, last=None, dialog=_USE_DEFAULT_DIALOG):
    """Run one recache_pass with fakes; returns (result, api, progress, dialogs)."""
    api = api or FakeApi()
    if last is not None:
        RecacheState(tmp_path).save(last)
    progress_seen = []
    dialog_seen = []

    def dialog_factory():
        d = FakeDialog() if dialog is _USE_DEFAULT_DIALOG else dialog
        dialog_seen.append(d)
        return d

    def progress_factory(d, idle_check):
        p = IdleAbortProgress(d, idle_check)
        progress_seen.append(p)
        return p

    result = recache_pass(settings, lambda: api, tmp_path, NOW,
                          lambda: idle, dialog_factory, progress_factory)
    return result, api, (progress_seen[0] if progress_seen else None), dialog_seen


def test_pass_runs_when_due_and_idle(tmp_path):
    last = datetime(2026, 9, 28, 12, 0)
    result, api, progress, _ = _run_pass(tmp_path, _settings(), idle=True, last=last)
    assert result is True
    assert len(api.calls) == 1
    assert api.calls[0]['clear_expired'] is True
    assert progress.idle_check() is True
    # slot marked done
    assert RecacheState(tmp_path).load() == datetime(2026, 9, 29, 3, 0)


def test_pass_blocked_by_idle_gate(tmp_path):
    last = datetime(2026, 9, 28, 12, 0)
    result, api, progress, _ = _run_pass(tmp_path, _settings(), idle=False, last=last)
    assert result is False
    assert api.calls == []
    # slot NOT marked done — retried on a later idle pass
    assert RecacheState(tmp_path).load() == last


def test_pass_idle_gate_disabled_setting(tmp_path):
    last = datetime(2026, 9, 28, 12, 0)
    result, api, _, _ = _run_pass(tmp_path, _settings({'recache.service.idle': 'false'}),
                               idle=False, last=last)
    assert result is True
    assert len(api.calls) == 1


def test_pass_not_due(tmp_path):
    result, api, _, _ = _run_pass(tmp_path, _settings(), idle=True, last=NOW)
    assert result is False
    assert api.calls == []


def test_pass_disabled_settings(tmp_path):
    for key in ['recache.enabled', 'recache.service']:
        result, api, _, _ = _run_pass(tmp_path, _settings({key: 'false'}), idle=True,
                                   last=datetime(2026, 9, 28, 12, 0))
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

    last = datetime(2026, 9, 28, 12, 0)
    result, api, progress, _ = _run_pass(tmp_path, _settings(), idle=True, api=AbortingApi(), last=last)
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


def test_idle_abort_progress_without_dialog_drops_updates():
    p = IdleAbortProgress(None, lambda: True)
    p.update(42.6, 'msg')  # must not raise
    assert p.iscanceled() is False


def test_pass_closes_dialog_after_run(tmp_path):
    last = datetime(2026, 9, 28, 12, 0)
    dialog = FakeDialog()
    result, _, _, seen = _run_pass(tmp_path, _settings(), idle=True, last=last, dialog=dialog)
    assert result is True
    assert seen == [dialog]
    assert dialog.closed is True


def test_pass_closes_dialog_even_when_aborted(tmp_path):
    class AbortingApi(FakeApi):
        def recache_items(self, progress=None, clear_expired=False):
            progress.was_aborted = True

    dialog = FakeDialog()
    last = datetime(2026, 9, 28, 12, 0)
    result, _, _, _ = _run_pass(tmp_path, _settings(), idle=True, api=AbortingApi(),
                                last=last, dialog=dialog)
    assert result is False
    assert dialog.closed is True


def test_pass_runs_without_dialog(tmp_path):
    last = datetime(2026, 9, 28, 12, 0)
    result, api, progress, seen = _run_pass(tmp_path, _settings(), idle=True, last=last, dialog=None)
    assert result is True
    assert seen == [None]
    assert progress.dialog is None
    assert len(api.calls) == 1

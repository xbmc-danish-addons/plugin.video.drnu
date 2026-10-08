"""Tests for the pre-7.1 recache migration in resources/lib/addon.py."""
from resources.lib import addon


def _settings_store(initial):
    store = dict(initial)

    def fake_set(key, value):
        store[key] = value

    return store, fake_set


def test_migrate_pre_7_1_enforces_defaults_and_clears_old_keys(monkeypatch):
    store, fake_set = _settings_store({
        'recache.cronjob': 'true',
        'recache.cronexpression': '0 4 * * *',
    })
    removed = []
    monkeypatch.setattr(addon, 'get_setting', store.get)
    monkeypatch.setattr(addon, 'set_setting', fake_set)
    monkeypatch.setattr(addon, 'remove_cronjob', lambda: removed.append(1))

    addon.migrate_pre_7_1()

    assert store['recache.time'] == '03:00'
    assert store['recache.service'] == 'true'
    assert store['recache.service.idle'] == 'true'
    assert store['recache.cronjob'] == ''
    assert store['recache.cronexpression'] == ''
    assert removed == [1]


def test_migrate_pre_7_1_removes_cronjob_even_without_settings(monkeypatch):
    store, fake_set = _settings_store({})
    removed = []
    monkeypatch.setattr(addon, 'get_setting', store.get)
    monkeypatch.setattr(addon, 'set_setting', fake_set)
    monkeypatch.setattr(addon, 'remove_cronjob', lambda: removed.append(1))

    addon.migrate_pre_7_1()

    assert removed == [1]
    assert store['recache.time'] == '03:00'


def _run_version_fixes(monkeypatch, first_run, settings_version, settings_V, addon_V):
    calls = []
    monkeypatch.setattr(addon, 'migrate_pre_7_1', lambda: calls.append(1))
    monkeypatch.setattr(addon, 'set_setting', lambda *a: None)

    class Fake:
        def _version_check(self):
            return first_run, settings_version, settings_V, addon_V

    Fake._version_change_fixes = addon.DrDkTvAddon._version_change_fixes
    Fake()._version_change_fixes()
    return calls


def test_version_fixes_migrates_from_pre_7_1(monkeypatch):
    calls = _run_version_fixes(
        monkeypatch, True, '7.0.0', addon.version('7.0.0'), addon.version('7.1.0'))
    assert calls == [1]


def test_version_fixes_migrates_when_jumping_past_7_1(monkeypatch):
    calls = _run_version_fixes(
        monkeypatch, True, '7.0.0', addon.version('7.0.0'), addon.version('7.2.0'))
    assert calls == [1]


def test_version_fixes_skips_when_already_on_7_1(monkeypatch):
    calls = _run_version_fixes(
        monkeypatch, True, '7.1.0', addon.version('7.1.0'), addon.version('7.1.1'))
    assert calls == []


def test_version_fixes_skips_without_version_change(monkeypatch):
    calls = _run_version_fixes(
        monkeypatch, False, '7.0.0', addon.version('7.0.0'), addon.version('7.1.0'))
    assert calls == []

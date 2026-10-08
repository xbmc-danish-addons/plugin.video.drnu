"""Unit tests for resources/lib/servicecleanup.py (no Kodi needed)."""
import os
import sqlite3
import time
from datetime import timedelta
from typing import Dict

import pytest
import requests.models
import requests_cache

from resources.lib import servicecleanup

CACHE_PREFIX = servicecleanup.CACHE_PREFIX
DB_FILE = servicecleanup.DB_FILE
MARKER = servicecleanup.MARKER_FILE
VACUUM_MARKER = servicecleanup.VACUUM_MARKER_FILE


def _response(url: str) -> requests.models.Response:
    r = requests.models.Response()
    r.url = url
    r.status_code = 200
    r._content = b'x' * 200000
    r.headers = {'Content-Type': 'application/json'}
    r.encoding = 'utf-8'
    req = requests.models.PreparedRequest()
    req.prepare(method='GET', url=url, hooks=[])
    r.request = req
    return r


def _seed_cache(cache_path, n: int):
    """Seed n cache entries directly through the requests-cache backend."""
    session = requests_cache.CachedSession(str(cache_path / CACHE_PREFIX), backend='sqlite')
    keys = []
    for i in range(n):
        key = f'key{i}'
        session.cache.save_response(key, _response(f'https://x.dk/api/{i}'))
        keys.append(key)
    session.close()
    return keys


def _backdate(cache_path, keys, hours: int) -> None:
    session = requests_cache.CachedSession(str(cache_path / CACHE_PREFIX), backend='sqlite')
    for key in keys:
        store, created = session.cache.responses[key]
        session.cache.responses[key] = (store, created - timedelta(hours=hours))
    session.close()


def _count(cache_path) -> int:
    session = requests_cache.CachedSession(str(cache_path / CACHE_PREFIX), backend='sqlite')
    n = len(list(session.cache.responses.keys()))
    session.close()
    return n


def _settings(overrides: Dict[str, str] = None):
    s = {'recache.enabled': 'true', 'recache.cleanup': '7', 'recache.expiration': '24'}
    if overrides:
        s.update(overrides)
    return s.get


def test_cleanup_removes_expired_and_shrinks_file(tmp_path):
    _seed_cache(tmp_path, n=3)
    marker = tmp_path / MARKER
    marker.write_text('seed')
    size_before = (tmp_path / DB_FILE).stat().st_size
    _backdate(tmp_path, ['key0', 'key1'], hours=48)

    assert servicecleanup.cleanup_cache(tmp_path, expire_hours=24) is True

    assert _count(tmp_path) == 1
    size_after = (tmp_path / DB_FILE).stat().st_size
    assert size_after < size_before * 0.6
    # VACUUM left no free pages behind and both markers were refreshed
    con = sqlite3.connect(str(tmp_path / DB_FILE))
    assert con.execute('PRAGMA freelist_count').fetchone()[0] == 0
    con.close()
    assert marker.read_text() != 'seed'
    assert (tmp_path / VACUUM_MARKER).read_text() != ''


def test_cleanup_without_marker_is_noop(tmp_path):
    _seed_cache(tmp_path, n=1)
    assert servicecleanup.cleanup_cache(tmp_path, expire_hours=24) is False
    assert _count(tmp_path) == 1


def test_cleanup_without_db_is_noop(tmp_path):
    (tmp_path / MARKER).write_text('x')
    assert servicecleanup.cleanup_cache(tmp_path, expire_hours=24) is False


def test_cleanup_keeps_everything_when_expiration_disabled(tmp_path):
    _seed_cache(tmp_path, n=2)
    (tmp_path / MARKER).write_text('x')
    assert servicecleanup.cleanup_cache(tmp_path, expire_hours=-1) is True
    assert _count(tmp_path) == 2
    assert (tmp_path / MARKER).read_text() != 'x'


def test_cleanup_failure_returns_false_and_keeps_marker(tmp_path, monkeypatch):
    _seed_cache(tmp_path, n=1)
    marker = tmp_path / MARKER
    marker.write_text('x')

    def boom(self, created_before):
        raise sqlite3.OperationalError('database is locked')

    monkeypatch.setattr('requests_cache.backends.sqlite.DbCache.remove_old_entries', boom)
    assert servicecleanup.cleanup_cache(tmp_path, expire_hours=24, log_func=lambda m: None) is False
    assert marker.read_text() == 'x'


def test_vacuum_missing_file(tmp_path):
    assert servicecleanup.vacuum_db(tmp_path / 'nope.sqlite') is False


def test_vacuum_releases_freed_pages(tmp_path):
    db = tmp_path / 't.sqlite'
    con = sqlite3.connect(str(db))
    con.execute('CREATE TABLE t (v BLOB)')
    con.execute('INSERT INTO t VALUES (?)', (b'x' * 100000,))
    con.commit()
    con.execute('DELETE FROM t')
    con.commit()
    assert con.execute('PRAGMA freelist_count').fetchone()[0] > 0
    con.close()
    assert servicecleanup.vacuum_db(db) is True
    con = sqlite3.connect(str(db))
    assert con.execute('PRAGMA freelist_count').fetchone()[0] == 0
    con.close()


def test_cleanup_due_no_marker(tmp_path):
    assert servicecleanup.cleanup_due(tmp_path, 7)


def test_cleanup_due_fresh_marker(tmp_path):
    (tmp_path / VACUUM_MARKER).write_text('x')
    assert not servicecleanup.cleanup_due(tmp_path, 7)


def test_cleanup_due_ignores_fresh_requests_cleaned(tmp_path):
    """The daily re-cache refreshes requests_cleaned; that must not postpone
    the VACUUM, which is gated on its own marker."""
    (tmp_path / MARKER).write_text('x')
    assert servicecleanup.cleanup_due(tmp_path, 7)


def test_cleanup_due_old_marker(tmp_path):
    marker = tmp_path / VACUUM_MARKER
    marker.write_text('x')
    old = time.time() - 8 * 24 * 3600
    os.utime(marker, (old, old))
    assert servicecleanup.cleanup_due(tmp_path, 7)
    # exactly cleanup_every days old counts as due
    old = time.time() - 7 * 24 * 3600
    os.utime(marker, (old, old))
    assert servicecleanup.cleanup_due(tmp_path, 7)
    # just under is not
    old = time.time() - 6.9 * 24 * 3600
    os.utime(marker, (old, old))
    assert not servicecleanup.cleanup_due(tmp_path, 7)


def test_cleanup_due_now_override(tmp_path):
    marker = tmp_path / VACUUM_MARKER
    marker.write_text('x')
    written = time.time() - 8 * 24 * 3600
    os.utime(marker, (written, written))
    assert servicecleanup.cleanup_due(tmp_path, 7)
    assert not servicecleanup.cleanup_due(tmp_path, 7, now=written + 1)


def test_run_cleanup_disabled(tmp_path):
    (tmp_path / MARKER).write_text('x')
    assert servicecleanup.run_cleanup(_settings({'recache.enabled': 'false'}), tmp_path) is False


def test_run_cleanup_not_due(tmp_path):
    (tmp_path / MARKER).write_text('x')
    assert servicecleanup.run_cleanup(_settings(), tmp_path) is False


def test_run_cleanup_due_runs(tmp_path):
    _seed_cache(tmp_path, n=1)
    marker = tmp_path / MARKER
    marker.write_text('x')
    old = time.time() - 8 * 24 * 3600
    os.utime(marker, (old, old))
    assert servicecleanup.run_cleanup(_settings(), tmp_path) is True
    assert _count(tmp_path) == 1  # nothing expired yet, but marker refreshed
    assert marker.read_text() != 'x'

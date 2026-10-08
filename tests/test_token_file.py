"""Tests for atomic token persistence and corrupt token-file recovery.

The service and the plugin share token.p; writing it in place could leave an
empty or partial file that a concurrent reader would fail to unpickle.
"""
import pickle

from resources.lib import tvapi

# conftest's addon_handle fixture patches Api.refresh_tokens class-wide to a
# no-op; keep the real one so this module can exercise it
_REAL_REFRESH_TOKENS = tvapi.Api.refresh_tokens


def _api(tmp_path):
    api = tvapi.Api.__new__(tvapi.Api)
    api.cachePath = tmp_path
    api.token_file = tmp_path / 'token.p'
    api.access_tokens = {'refresh_token': 'r'}
    api._user_token = None
    return api


def test_write_tokens_replaces_atomically(tmp_path):
    api = _api(tmp_path)
    api.write_tokens([{'Token': 't'}])

    with api.token_file.open('rb') as fh:
        assert pickle.load(fh) == [[{'Token': 't'}], {'refresh_token': 'r'}]
    # no temp file is left behind
    assert list(tmp_path.glob('*.tmp')) == []


def test_write_tokens_does_not_truncate_existing_file_first(tmp_path):
    """The previous file must stay readable until the replace happens."""
    api = _api(tmp_path)
    api.token_file.write_bytes(pickle.dumps([{'Token': 'old'}, {}]))

    # a reader holding the file open across the write still sees valid data
    with api.token_file.open('rb') as fh:
        api.write_tokens([{'Token': 'new'}])
        assert pickle.load(fh) == [{'Token': 'old'}, {}]


def test_write_tokens_uses_a_per_process_temp_file(tmp_path, monkeypatch):
    """The service and the plugin share token.p but are separate processes;
    a shared token.tmp could be corrupted by interleaved writes and then
    installed over token.p. The temp name must be per process."""
    monkeypatch.setattr(tvapi.os, 'getpid', lambda: 4242)
    api = _api(tmp_path)
    seen = {}
    real_replace = tvapi.os.replace

    def spy_replace(src, dst):
        seen['src'] = str(src)
        seen['dst'] = str(dst)
        real_replace(src, dst)

    monkeypatch.setattr(tvapi.os, 'replace', spy_replace)
    api.write_tokens([{'Token': 't'}])

    # a write must never target the plain shared name
    assert seen['src'].endswith('token.p.4242.tmp')
    assert seen['dst'].endswith('token.p')


def test_refresh_tokens_recovers_from_corrupt_file(tmp_path, monkeypatch):
    api = _api(tmp_path)
    api.token_file.write_bytes(b'\x80\x04garbage')  # truncated pickle
    api.get_setting = lambda name: ''
    api.user = ''
    api.password = ''
    api._user_name = ''
    api.read_tokens = lambda tokens: None
    api.write_tokens = lambda tokens: None

    requested = []

    def request_tokens():
        requested.append(True)
        api._user_token = 'fresh'
        return None

    api.request_tokens = request_tokens

    _REAL_REFRESH_TOKENS(api)

    assert requested == [True]
    assert api._user_token == 'fresh'

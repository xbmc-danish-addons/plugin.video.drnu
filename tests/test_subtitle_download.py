"""Tests for error handling in subtitles.handle_subtitle_vtts.

A subtitle download or file write failure must never stop playback: the video
can still use its embedded subtitle streams. The result is keyed by language
so a skipped download cannot shift which language a caller selects.
"""
import requests

from resources.lib.subtitles import handle_subtitle_vtts

VTT = b'WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n'


class FakeResponse:
    def __init__(self, status_code=200, content=VTT):
        self.status_code = status_code
        self.content = content
        self.closed = False

    def close(self):
        self.closed = True


class FakeSession:
    """Returns queued responses (or raises queued exceptions) in order."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, url, timeout=None):
        result = self.responses[self.calls]
        self.calls += 1
        if isinstance(result, Exception):
            raise result
        return result


def tr(string_id):
    return f'tr{string_id}'


def subs(*languages):
    return [{'language': lang, 'link': f'https://subs/{i}'} for i, lang in enumerate(languages)]


def test_result_is_keyed_by_language(tmp_path):
    session = FakeSession([FakeResponse()])
    out = handle_subtitle_vtts(subs('DanishLanguageSubtitles'), tmp_path, tr, session)
    assert list(out) == ['DanishLanguageSubtitles']
    assert out['DanishLanguageSubtitles'].endswith('.srt')


def test_failed_download_is_skipped_and_loop_continues(tmp_path):
    session = FakeSession([FakeResponse(status_code=500), FakeResponse()])
    out = handle_subtitle_vtts(subs('DanishLanguageSubtitles', 'ForeignLanguageSubtitles'), tmp_path, tr, session)
    # the 500 is dropped, the following subtitle is still written under its own key
    assert list(out) == ['ForeignLanguageSubtitles']
    assert session.calls == 2


def test_non_200_response_is_closed(tmp_path):
    failed = FakeResponse(status_code=404)
    session = FakeSession([failed])
    handle_subtitle_vtts(subs('DanishLanguageSubtitles'), tmp_path, tr, session)
    assert failed.closed is True


def test_request_exception_is_swallowed(tmp_path):
    session = FakeSession([requests.ConnectionError('boom'), FakeResponse()])
    out = handle_subtitle_vtts(subs('DanishLanguageSubtitles', 'ForeignLanguageSubtitles'), tmp_path, tr, session)
    assert list(out) == ['ForeignLanguageSubtitles']


def test_file_write_error_is_swallowed(tmp_path):
    missing_dir = tmp_path / 'does-not-exist'
    session = FakeSession([FakeResponse()])
    out = handle_subtitle_vtts(subs('DanishLanguageSubtitles'), missing_dir, tr, session)
    assert out == {}

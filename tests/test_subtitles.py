"""Unit tests for resources/lib/subtitles.py (no Kodi needed)."""
from resources.lib.subtitles import vtt2srt

VTT = (
    "WEBVTT\r\n"
    "\r\n"
    "1\r\n"
    "00:00:01.000 --> 00:00:02.000\r\n"
    "Hello\r\n"
    "\r\n"
    "2\r\n"
    "00:00:03.000 --> 00:00:04.000\r\n"
    "World\r\n"
)


def test_vtt2srt():
    srt = vtt2srt(VTT)
    assert srt == (
        '1\n'
        '00:00:01,000 --> 00:00:02,000\n'
        'Hello\n'
        '\n'
        '2\n'
        '00:00:03,000 --> 00:00:04,000\n'
        'World'
    )


def test_vtt2srt_accepts_bytes():
    srt = vtt2srt(VTT.encode('utf-8'))
    assert srt.startswith('1\n00:00:01,000')

"""Unit tests for resources/lib/subtitles.py (no Kodi needed)."""
from resources.lib.subtitles import resolve_subtitle_action, vtt2srt

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

# subs: language -> stream index, as built by playVideo
SUBS_DK_COMBINED_FI = {'DanishLanguageSubtitles': 0, 'CombinedLanguageSubtitles': 1, 'ForeignLanguageSubtitles': 2}
SUBS_DK_ONLY = {'DanishLanguageSubtitles': 0, 'CombinedLanguageSubtitles': 1}
SUBS_FI_ONLY = {'ForeignLanguageSubtitles': 0}
SUBS_NONE = {}

# local_subtitles: language -> downloaded SRT path
LOCAL_DK = {'DanishLanguageSubtitles': 'dk.srt'}
LOCAL_DK_COMBINED = {'DanishLanguageSubtitles': 'dk.srt', 'CombinedLanguageSubtitles': 'combined.srt'}
LOCAL_FI = {'ForeignLanguageSubtitles': 'fi.srt'}

DEFAULTS = {
    'disable.kids.subtitles': False,
    'enable.subtitles': True,
    'enable.localsubtitles': True,
    'inputstream': 0,
}


def settings(**overrides):
    s = dict(DEFAULTS)
    s.update(overrides)
    return s


def test_kids_channel_disables_subtitles():
    # kids_channel only forces subtitles off when the setting is on
    assert resolve_subtitle_action(settings(), SUBS_DK_COMBINED_FI, True, LOCAL_DK) == ('local', 'dk.srt')
    s = _with(settings(), {'disable.kids.subtitles': True})
    assert resolve_subtitle_action(s, SUBS_DK_COMBINED_FI, True, LOCAL_DK) == ('off', None)


def _with(base, updates):
    s = dict(base)
    s.update(updates)
    return s


def test_enable_subtitles_prefers_danish_local_file():
    # selection is by language, not list position
    assert resolve_subtitle_action(settings(), SUBS_DK_COMBINED_FI, False, LOCAL_DK_COMBINED) == ('local', 'dk.srt')


def test_enable_subtitles_falls_back_to_stream_without_local_files():
    s = _with(settings(), {'enable.localsubtitles': False})
    assert resolve_subtitle_action(s, SUBS_DK_COMBINED_FI, False, {}) == ('stream', 0)


def test_enable_subtitles_empty_local_map_falls_back_to_stream():
    # the pre-refactor code indexed [-1] into an empty list here (IndexError);
    # falling back to the embedded stream is the sane behavior
    assert resolve_subtitle_action(settings(), SUBS_DK_COMBINED_FI, False, {}) == ('stream', 0)


def test_enable_subtitles_stream_priority_danish_first():
    assert resolve_subtitle_action(settings(), SUBS_DK_COMBINED_FI, False, {}) == ('stream', 0)
    assert resolve_subtitle_action(settings(), SUBS_DK_COMBINED_FI, False, {}) != ('stream', 2)


def test_enable_subtitles_no_matching_language_leaves_subtitles_untouched():
    assert resolve_subtitle_action(settings(), SUBS_NONE, False, {}) == (None, None)


def test_enable_subtitles_uses_foreign_file_when_only_foreign_downloaded():
    """Danish subtitle missing but the foreign file present: the priority
    loop must reach the foreign entry rather than give up."""
    assert resolve_subtitle_action(settings(), SUBS_FI_ONLY, False, LOCAL_FI) == ('local', 'fi.srt')


def test_subtitles_disabled_foreign_uses_stream():
    s = _with(settings(), {'enable.subtitles': False, 'enable.localsubtitles': False})
    assert resolve_subtitle_action(s, SUBS_FI_ONLY, False, {}) == ('stream', 0)


def test_subtitles_disabled_foreign_uses_foreign_local_file():
    s = _with(settings(), {'enable.subtitles': False})
    assert resolve_subtitle_action(s, SUBS_FI_ONLY, False, LOCAL_FI) == ('local', 'fi.srt')


def test_subtitles_disabled_skips_danish_file_for_foreign_stream():
    """The review finding: with only the Danish file downloaded, the foreign
    translation must come from the embedded stream, not the Danish file at
    position 0."""
    s = _with(settings(), {'enable.subtitles': False})
    assert resolve_subtitle_action(s, SUBS_FI_ONLY, False, LOCAL_DK) == ('stream', 0)


def test_subtitles_disabled_no_foreign_turns_off():
    s = _with(settings(), {'enable.subtitles': False})
    assert resolve_subtitle_action(s, SUBS_DK_ONLY, False, LOCAL_DK) == ('off', None)
    assert resolve_subtitle_action(s, SUBS_NONE, False, {}) == ('off', None)


def test_inputstream_1_implies_local_subtitles():
    s = _with(settings(), {'enable.localsubtitles': False, 'inputstream': 1})
    assert resolve_subtitle_action(s, SUBS_DK_COMBINED_FI, False, LOCAL_DK) == ('local', 'dk.srt')


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

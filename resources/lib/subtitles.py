#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""WebVTT to SRT subtitle conversion and subtitle file handling."""

import re

LOCAL_SUBTITLE_LANGUAGES = ['DanishLanguageSubtitles', 'CombinedLanguageSubtitles']


def vtt2srt(vtt):
    """Convert a WebVTT subtitle (str or bytes) to SRT format."""
    if isinstance(vtt, bytes):
        vtt = vtt.decode('utf-8')
    srt = vtt.replace("\r\n", "\n")
    srt = re.sub(r'([\d]+)\.([\d]+)', r'\1,\2', srt)
    srt = re.sub(r'WEBVTT\n\n', '', srt)
    srt = re.sub(r'^\d+\n', '', srt)
    srt = re.sub(r'\n\d+\n', '\n', srt)
    srt = re.sub(r'\n([\d]+)', r'\nputINDEXhere\n\1', srt)

    srtout = ['1']
    idx = 2
    for line in srt.splitlines():
        if line == 'putINDEXhere':
            line = str(idx)
            idx += 1
        srtout.append(line)
    return '\n'.join(srtout)


def handle_subtitle_vtts(subs, cache_path, tr_func, session):
    """Download subtitle VTTs and store them as local SRT files.

    Returns the list of written SRT file paths (str). Download of one
    subtitle failing stops the loop, mirroring the original behavior.
    """
    subtitles_uri = []
    for sub in subs:
        tr_id = 30050 if sub['language'] in LOCAL_SUBTITLE_LANGUAGES else 30051
        name = f'{cache_path}/{tr_func(tr_id)}.da.srt'
        u = session.get(sub['link'], timeout=10)
        if u.status_code != 200:
            u.close()
            break
        srt = vtt2srt(u.content)
        with open(name, 'wb') as fh:
            fh.write(srt.encode('utf-8'))
        u.close()
        subtitles_uri.append(name)
    return subtitles_uri

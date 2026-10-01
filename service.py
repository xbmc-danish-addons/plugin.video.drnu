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
"""Kodi service: request-cache maintenance and background re-cache.

Runs for the lifetime of Kodi and hourly:
- expires old responses and VACUUMs the requests-cache sqlite database
- runs the re-cache crawl when 'recache.cronexpression' is due, gated on
  Kodi being idle (setting recache.service.idle), so an always-on media
  center keeps its cache fresh without the cronxbmc job
"""
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import xbmc
import xbmcaddon
import xbmcgui
from xbmcvfs import translatePath

from resources.lib import tvapi
from resources.lib.kodiutils import get_setting, log, tr
from resources.lib.recachescheduler import recache_pass
from resources.lib.servicecleanup import run_cleanup

CHECK_INTERVAL_SECONDS = 60 * 60
IDLE_SECONDS = 300


def idle_and_not_playing() -> bool:
    """True when Kodi has been idle long enough and nothing is playing."""
    if xbmc.getCondVisibility('Player.playing'):
        return False
    return xbmc.getGlobalIdleTime() >= IDLE_SECONDS


def cleanup_once(cache_path: Path) -> None:
    """One cache maintenance pass, skipped while playback is active to avoid
    sqlite contention with the addon."""
    if xbmc.getCondVisibility('Player.playing'):
        return
    if run_cleanup(get_setting, cache_path, log):
        log('servicecleanup: expired and vacuumed the request cache db')


def make_bg_dialog() -> Optional[xbmcgui.DialogProgressBG]:
    """Create the background progress dialog, or None if Kodi refuses.

    DialogProgressBG.create() raises RuntimeError outside a GUI context
    (e.g. a headless service start); the crawl itself does not need the
    dialog, so degrade to running without progress instead of failing.
    """
    dialog = xbmcgui.DialogProgressBG()
    try:
        dialog.create('DR TV', tr(30524))
        return dialog
    except RuntimeError:
        return None


def recache_once(cache_path: Path) -> None:
    """Run the scheduled re-cache crawl when due (idle-gated by default)."""
    if recache_pass(get_setting, lambda: tvapi.Api(cache_path, tr, get_setting, log),
                    cache_path, datetime.now(), idle_and_not_playing,
                    make_bg_dialog):
        log('servicecleanup: background re-cache finished')


def run(monitor: xbmc.Monitor, cleanup: Callable[[], None], interval_seconds: int) -> None:
    """Service loop: clean on startup, then once per interval until Kodi exits."""
    while not monitor.abortRequested():
        try:
            cleanup()
        except Exception:
            log(traceback.format_exc(), xbmc.LOGERROR)
        monitor.waitForAbort(interval_seconds)


def main() -> None:
    cache_path = Path(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
    monitor = xbmc.Monitor()
    run(monitor, lambda: (cleanup_once(cache_path), recache_once(cache_path)), CHECK_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()

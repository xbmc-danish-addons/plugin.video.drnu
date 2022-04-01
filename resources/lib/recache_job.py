from tvapi import Api

import os

import xbmc
import xbmcaddon
import xbmcgui

from xbmcvfs import translatePath

def tr(id):
    if isinstance(id, list):
        return '\n'.join([addon.getLocalizedString(item) for item in id])
    return addon.getLocalizedString(id)

addon = xbmcaddon.Addon('plugin.video.drnu')

cachepath = translatePath(addon.getAddonInfo("Profile"))
if not os.path.exists(cachepath):
    os.makedirs(cachepath)

api = Api(cachepath, tr)
progress = xbmcgui.DialogProgress()
progress.create("video.drnu recaching...")
progress.update(0)

used_time = api.recache_requests(cache_urls=False, cache_episodes=True, clear_expired=False, verbose=True, progress=progress)

progress.update(100)
progress.close()

#xbmcgui.Dialog().ok("finished re-caching in ", f'{used_time:.1f} seconds'))

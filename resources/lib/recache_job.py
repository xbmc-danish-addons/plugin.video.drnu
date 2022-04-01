from tvapi import Api
from addon import tr
import os

import xbmc
import xbmcaddon
import xbmcgui

from xbmcvfs import translatePath

addon = xbmcaddon.Addon('plugin.video.drnu')

cachepath = translatePath(addon.getAddonInfo("Profile"))
if not os.path.exists(cachepath):
    os.makedirs(cachepath)

api = Api(cachepath, tr)
used_time = api.recache_requests(cache_urls=False, cache_episodes=False, clear_expired=False, verbose=False)

xbmcgui.Dialog().ok("finished re-caching in ")

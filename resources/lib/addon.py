#
#      Copyright (C) 2014 Tommy Winther, msj33, TermeHansen
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
import datetime
import os
import pickle
import re
import sys
import traceback

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import json

from resources.lib import tvapi
from resources.lib import tvgui

if sys.version_info.major == 2:
    # python 2
    import urlparse
    from xbmc import translatePath
    compat_str = unicode
else:
    import urllib.parse as urlparse
    from xbmcvfs import translatePath
    compat_str = str


addon = xbmcaddon.Addon()
get_setting = addon.getSetting
addon_path = addon.getAddonInfo('path')
addon_name = addon.getAddonInfo('name')


def tr(id):
    if isinstance(id, list):
        return '\n'.join([addon.getLocalizedString(item) for item in id])
    return addon.getLocalizedString(id)


def bool_setting(name):
    return get_setting(name) == 'true'


def make_notice(object):
    xbmc.log(str(object), xbmc.LOGINFO)


class DrDkTvAddon(object):
    def __init__(self, plugin_url, plugin_handle):
        self._plugin_url = plugin_url
        self._plugin_handle = plugin_handle

        self.cache_path = translatePath(addon.getAddonInfo('profile'))
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

        self.favorites_path = os.path.join(self.cache_path, 'favorites.pickle')
        self.recent_path = os.path.join(self.cache_path, 'recent.pickle')
        self.fanart_image = os.path.join(addon_path, 'resources', 'fanart.jpg')

        self.api = tvapi.Api(self.cache_path, tr)
        self.api2 = tvapi.NewApi(self.cache_path, tr)
        self.favorites = list()
        self.recentlyWatched = list()

        self.menuItems = list()
        runScript = "RunAddon(plugin.video.drnu,?show=areaselector&random={:d})".format(self._plugin_handle)
        self.menuItems.append((tr(30511), runScript))

        # Area Selector
        self.area_item = xbmcgui.ListItem(tr(30101), offscreen=True)
        self.area_item.setArt({'fanart': self.fanart_image, 'icon': os.path.join(
            addon_path, 'resources', 'icons', 'all.png')})

        self._load()

    def _save(self):
        # save favorites
        self.favorites.sort()
        pickle.dump(self.favorites, open(self.favorites_path, 'wb'))

        self.recentlyWatched = self.recentlyWatched[0:25]  # Limit to 25 items
        pickle.dump(self.recentlyWatched, open(self.recent_path, 'wb'))

    def _load(self):
        # load favorites
        if os.path.exists(self.favorites_path):
            try:
                self.favorites = pickle.load(open(self.favorites_path, 'rb'))
            except Exception:
                pass

        # load recently watched
        if os.path.exists(self.recent_path):
            try:
                self.recentlyWatched = pickle.load(open(self.recent_path, 'rb'))
            except Exception:
                pass

    def showAreaSelector(self):
        gui = tvgui.AreaSelectorDialog()
        gui.doModal()
        areaSelected = gui.areaSelected
        del gui

        if areaSelected == 'none':
            pass
        elif areaSelected == 'drtv':
            self.showMainMenu()
        else:
            items = self.api.getChildrenFrontItems('dr-' + areaSelected)
            self.listSeries(items, add_area_selector=bool_setting('enable.areaitem'))

    def showMainMenu(self):
        items = list()
        # Live TV
        item = xbmcgui.ListItem(tr(30027), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': os.path.join(addon_path, 'resources', 'icons', 'livetv.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=liveTV', item, True))

        # A-Z Program Series
        item = xbmcgui.ListItem(tr(30000), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': os.path.join(addon_path, 'resources', 'icons', 'all.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=listAZ', item, True))
        for hitem in self.api2.get_home():
            if hitem['path']:
                item = xbmcgui.ListItem(hitem['title'], offscreen=True)
                item.setArt({'fanart': self.fanart_image, 'icon': os.path.join(
                    addon_path, 'resources', 'icons', 'star.png')})
                item.addContextMenuItems(self.menuItems, False)
                items.append((self._plugin_url + '?listVideos2=' + hitem['path'], item, True))

        # Search videos
        item = xbmcgui.ListItem(tr(30003), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': os.path.join(addon_path, 'resources', 'icons', 'search.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=search', item, True))

        # Recently watched Program Series
        item = xbmcgui.ListItem(tr(30007), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': os.path.join(
            addon_path, 'resources', 'icons', 'eye-star.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=recentlyWatched', item, True))

        # Favorite Program Series
        item = xbmcgui.ListItem(tr(30008), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': os.path.join(
            addon_path, 'resources', 'icons', 'plusone.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=favorites', item, True))

        if bool_setting('enable.areaitem'):
            items.append((self._plugin_url + '?show=areaselector', self.area_item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showFavorites(self):
        self._load()
        if not self.favorites:
            xbmcgui.Dialog().ok(addon_name, tr(30013))
            xbmcplugin.endOfDirectory(self._plugin_handle, succeeded=False)
        else:
            series = []
            for slug in self.favorites:
                series.extend(self.api.searchSeries(slug))
            self.listSeries(series, addToFavorites=False)

    def showRecentlyWatched(self):
        self._load()
        videos = list()
        for slug in self.recentlyWatched:
            try:
                item = self.api.getEpisode(slug)
                if item is None:
                    self.recentlyWatched.remove(slug)
                else:
                    videos.append(item)
            except tvapi.ApiException:
                # probably a 404 - non-existent slug
                self.recentlyWatched.remove(slug)

        self._save()
        if not videos:
            xbmcgui.Dialog().ok(addon_name, tr([30013, 30020]))
            xbmcplugin.endOfDirectory(self._plugin_handle, succeeded=False)
        else:
            self.listEpisodes(videos)

    def showLiveTV(self):
        items = list()
        HLS = 'HLS_subtitles' if bool_setting('enable.subtitles') else 'HLS'
        for channel in self.api.getLiveTV():
            if channel['WebChannel']:
                continue

            server = None
            for streamingServer in channel['StreamingServers']:
                if streamingServer['LinkType'] == HLS:
                    server = streamingServer
                    break

            if server is None:
                continue

            item = xbmcgui.ListItem(channel['Title'], offscreen=True)
            fanart_h = int(get_setting('fanart.size'))
            fanart_w = int(fanart_h*16/9)
            item.setArt({'thumb': self.api.redirectImageUrl(channel['PrimaryImageUri'], 640, 360),
                         'icon': self.api.redirectImageUrl(channel['PrimaryImageUri'], 75, 42),
                         'fanart': self.api.redirectImageUrl(channel['PrimaryImageUri'], fanart_w, fanart_h)})
            item.addContextMenuItems(self.menuItems, False)

            url = server['Server'] + '/' + server['Qualities'][0]['Streams'][0]['Stream']
            items.append((url, item, False))

        items.sort(key=lambda x: x[1].getLabel().replace(' ', ''))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showAZ(self):
        # All Program Series
        iconImage = os.path.join(addon_path, 'resources', 'icons', 'all.png')
        items = list()
        for programIndex in self.api.getProgramIndexes():
            item = xbmcgui.ListItem(programIndex['Title'], offscreen=True)
            item.setArt({'fanart': self.fanart_image, 'icon': iconImage})
            item.addContextMenuItems(self.menuItems, False)

            url = self._plugin_url + '?listProgramSeriesByLetter=' + programIndex['_Param']
            items.append((url, item, True))
        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def searchSeries(self):
        keyboard = xbmc.Keyboard('', tr(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            self.listSeries(self.api.getSeries(keyword))

    def kodi_item(self, item, is_season=False):
        menuItems = list(self.menuItems)
        isFolder = item['type'] not in ['program', 'episode']
        if item['type'] in ['ImageEntry', 'TextEntry'] or item['title'] == '':
            return None

        title = item['title']
        if item['type'] == 'season':
            title += f" {item['seasonNumber']}"
        listItem = xbmcgui.ListItem(title, offscreen=True)
        if 'images' in item:
            listItem.setArt({'thumb': item['images']['tile'],
                            'icon': item['images']['tile'],
                            'fanart': item['images']['wallpaper']
                            })
        else:
            listItem.setArt({'fanart': self.fanart_image, 'icon': os.path.join(
                    addon_path, 'resources', 'icons', 'star.png')})

        make_notice(f"{title} -- {item['type']} {isFolder}")

        if isFolder:
            if title in self.favorites:
                runScript = compat_str("RunPlugin(plugin://plugin.video.drnu/?delfavorite={})").format(title)
                menuItems.append((tr(30201), runScript))
            else:
                runScript = compat_str("RunPlugin(plugin://plugin.video.drnu/?addfavorite={})").format(title)
                menuItems.append((tr(30200), runScript))
            if 'path' in item:
                url = self._plugin_url + f"?listVideos2={item['path']}&seasons={is_season}"
            elif 'list' in item and 'path' in item['list']:
                url = self._plugin_url + f"?listVideos2={item['list']['path']}&seasons={is_season}"
            else:
                return None
        else:
            infoLabels = {
                'title': item['title']
            }
            if 'shortDescription' in item:
                infoLabels['plot'] = item['shortDescription']
            if 'BroadcastTimeDK' in item and item['BroadcastTimeDK'] is not None:
                broadcastTime = self.parseDate(item['BroadcastTimeDK'])
                if broadcastTime:
                    infoLabels['date'] = broadcastTime.strftime('%d.%m.%Y')
                    infoLabels['aired'] = broadcastTime.strftime('%Y-%m-%d')
                    infoLabels['year'] = int(broadcastTime.strftime('%Y'))
            kids = False
            if 'classification' in item:
                kids = item['classification']['code'] in ['DR-Ramasjang', 'DR-Minisjang']
            url = self._plugin_url + f"?playVideo={item['id']}&kids={str(kids)}"
            listItem.setInfo('video', infoLabels)
            listItem.setProperty('IsPlayable', 'true')

        listItem.addContextMenuItems(menuItems, False)
        return (url, listItem, isFolder,)

    def listEpisodes(self, items, addSortMethods=False, seasons=False):
        directoryItems = list()
        for item in items:
            gui_item = self.kodi_item(item, is_season=seasons)
            if gui_item is not None:
                directoryItems.append(gui_item)

        xbmcplugin.addDirectoryItems(self._plugin_handle, directoryItems)
        if addSortMethods:
            xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_DATE)
            xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def playVideo(self, id, kids_channel):
        self.updateRecentlyWatched(id)
        video = self.api2.getVideoUrl(id)
        kids_channel = kids_channel == 'True'

        with open('debug', 'w') as fh:
            fh.write(id + '\n')
            fh.write(str(kids_channel) + '\n')
            fh.write(str(video['url']) + '\n')
        if not video['url']:
            self.displayError(tr(30904))
            return

        item = xbmcgui.ListItem(path=video['url'], offscreen=True)
#        item.setArt({'thumb': api_item['PrimaryImageUri']})

        if not all([bool_setting('disable.kids.subtitles') and kids_channel]):
            if video['SubtitlesUri']:
                if bool_setting('enable.subtitles'):
                    item.setSubtitles(video['SubtitlesUri'][::-1])
                else:
                    item.setSubtitles(video['SubtitlesUri'])
        xbmcplugin.setResolvedUrl(self._plugin_handle, video['url'] is not None, item)

    # Supported slugs are dr1, dr2 and dr-ramasjang
    def playLiveTV(self, slug):
        item = None
        url = None
        HLS = 'HLS_subtitles' if bool_setting('enable.subtitles') else 'HLS'
        for channel in self.api.getLiveTV():
            # If the channel has the right slug, play the channel
            if channel['Slug'] == slug:
                server = None
                for streamingServer in channel['StreamingServers']:
                    if streamingServer['LinkType'] == HLS:
                        server = streamingServer
                        break
                if server is None:
                    continue

                url = server['Server'] + '/' + server['Qualities'][0]['Streams'][0]['Stream']
                item = xbmcgui.ListItem(channel['Title'], path=url, offscreen=True)
                item.setArt({'fanart': channel['PrimaryImageUri'], 'icon': channel['PrimaryImageUri']})
                item.addContextMenuItems(self.menuItems, False)
                break
        if item:
            xbmcplugin.setResolvedUrl(self._plugin_handle, True, item)
        else:
            self.displayError('{} {}'.format(tr(30905), slug))

    def parseDate(self, dateString):
        if dateString is not None:
            try:
                m = re.search('(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)', dateString)
                year = int(m.group(1))
                month = int(m.group(2))
                day = int(m.group(3))
                hours = int(m.group(4))
                minutes = int(m.group(5))
                seconds = int(m.group(6))
                return datetime.datetime(year, month, day, hours, minutes, seconds)
            except ValueError:
                return None
        else:
            return None

    def addFavorite(self, key):
        self._load()
        if key not in self.favorites:
            self.favorites.append(key)
        self._save()
        xbmcgui.Dialog().ok(addon_name, tr([30008, 30009]))

    def delFavorite(self, key):
        self._load()
        if key in self.favorites:
            self.favorites.remove(key)
        self._save()
        xbmcgui.Dialog().ok(addon_name, tr([30008, 30010]))

    def updateRecentlyWatched(self, assetUri):
        self._load()
        if assetUri in self.recentlyWatched:
            self.recentlyWatched.remove(assetUri)
        self.recentlyWatched.insert(0, assetUri)
        self._save()

    def displayError(self, message='n/a'):
        heading = 'API error'
        xbmcgui.Dialog().ok(heading, '\n'.join([tr(30900), tr(30901), message]))

    def displayIOError(self, message='n/a'):
        heading = 'I/O error'
        xbmcgui.Dialog().ok(heading, '\n'.join([tr(30902), tr(30903), message]))

    def route(self, query):
        try:
            PARAMS = dict(urlparse.parse_qsl(query[1:]))
            if 'show' in PARAMS:
                if PARAMS['show'] == 'liveTV':
                    self.showLiveTV()
                elif PARAMS['show'] == 'listAZ':
                    self.showAZ()
                elif PARAMS['show'] == 'latest':
                    self.listEpisodes(self.api.getLatestPrograms(), addSortMethods=False)
                elif PARAMS['show'] == 'mostViewed':
                    self.listEpisodes(self.api.getMostViewed())
                elif PARAMS['show'] == 'highlights':
                    self.listEpisodes(self.api.getSelectedList())
                elif PARAMS['show'] == 'search':
                    self.searchSeries()
                elif PARAMS['show'] == 'favorites':
                    self.showFavorites()
                elif PARAMS['show'] == 'recentlyWatched':
                    self.showRecentlyWatched()
                elif PARAMS['show'] == 'areaselector':
                    self.showAreaSelector()
                elif PARAMS['show'] == 'themes':
                    self.showThemes()

            elif 'listThemeSeries' in PARAMS:
                self.listSeries(self.api.getEpisodes(PARAMS['listThemeSeries']))

            elif 'listProgramSeriesByLetter' in PARAMS:
                self.listSeries(self.api.getSeries(PARAMS['listProgramSeriesByLetter']))

            elif 'listVideos' in PARAMS:
                self.listEpisodes(self.api.getEpisodes(PARAMS['listVideos']))

            elif 'listVideos2' in PARAMS:
                seasons = PARAMS.get('seasons', 'False')
                make_notice(f"{PARAMS['listVideos2']}  {seasons}")
                entries = self.api2.get_programcard(PARAMS['listVideos2'])['entries']
                if len(entries) > 1:
                    self.listEpisodes(entries)
                else: 
                    item = entries[0]
                    if item['type'] == 'ItemEntry':
                        # if item['item']['type'] == 'show':
                        #     self.listEpisodes(item['item']['seasons']['items'])
                        if item['item']['type'] == 'season':
                            if seasons == 'True' or item['item']['show']['availableSeasonCount'] == 1:
                                make_notice(f"here  ")
                                self.listEpisodes(item['item']['episodes']['items'], seasons=False)
                                make_notice(f"here2  ")
                            else:
                                make_notice(f"here 3 ")
                                self.listEpisodes(item['item']['show']['seasons']['items'], seasons=True)
                                make_notice(f"here 4 ")
                        else:
                            raise tvapi.ApiException(f"{item['item']['type']} unknown")

                    elif item['type'] == 'ListEntry':
                        self.listEpisodes(item['list']['items'])
                    else:
                        raise tvapi.ApiException(f"{item['type']} unknown")

            elif 'playVideo' in PARAMS:
                self.playVideo(PARAMS['playVideo'], PARAMS['kids'])

            # Supported slugs are dr1, dr2 and dr-ramasjang
            elif 'playLiveTV' in PARAMS:
                self.playLiveTV(PARAMS['playLiveTV'])

            elif 'addfavorite' in PARAMS:
                self.addFavorite(PARAMS['addfavorite'])

            elif 'delfavorite' in PARAMS:
                self.delFavorite(PARAMS['delfavorite'])

            else:
                try:
                    area = int(get_setting('area'))
                except:
                    area = 0

                if area == 0:
                    self.showAreaSelector()
                elif area == 1:
                    self.showMainMenu()
                elif area == 2:
                    items = self.api.getChildrenFrontItems('dr-ramasjang')
                    self.listSeries(items, add_area_selector=True)
                elif area == 3:
                    items = self.api.getChildrenFrontItems('dr-ultra')
                    self.listSeries(items, add_area_selector=True)

#        except tvapi.ApiException as ex:
#            self.displayError(str(ex))

#        except IOError as ex:
#            self.displayIOError(str(ex))

        except Exception as ex:
            raise ex
#            stack = traceback.format_exc()
#            heading = 'drnu addon crash'
#            xbmcgui.Dialog().ok(heading, '\n'.join([tr(30906), tr(30907)]))

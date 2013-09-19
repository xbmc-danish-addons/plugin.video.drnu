#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
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
import pickle
import os
import sys
import urlparse
import re
import datetime

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import tvapi
import buggalo

LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '\xC3\x86', '\xC3\x98', '\xC3\x85']


class NuAddon(object):
    def __init__(self):
        self.api = tvapi.TvApi()

        # load favorites
        self.favorites = list()
        if os.path.exists(FAVORITES_PATH):
            try:
                self.favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
            except Exception:
                pass

        # load recently watched
        self.recentlyWatched = list()
        if os.path.exists(RECENT_PATH):
            try:
                self.recentlyWatched = pickle.load(open(RECENT_PATH, 'rb'))
            except Exception:
                pass

    def _save(self):
        # save favorites
        self.favorites.sort()
        pickle.dump(self.favorites, open(FAVORITES_PATH, 'wb'))

        self.recentlyWatched = self.recentlyWatched[0:25]  # Limit to ten items
        pickle.dump(self.recentlyWatched, open(RECENT_PATH, 'wb'))

    def showMainMenu(self):
        items = list()
        # A-Z Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30000),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=listAZ', item, True))
        # Most viewed
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30011),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=mostViewed', item, True))
        # # Search videos
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30003),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'search.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=search', item, True))
        # Recently watched Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30007),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons',
                                                       'eye-star.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=recentlyWatched', item, True))
        # Favorite Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30008),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'plusone.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=favorites', item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def showProgramSeriesVideos(self, slug):
        self.listVideos(self.api.programCardRelations(slug))

    def showMostViewedVideos(self):
        self.listVideos(self.api.getMostViewedProgramCards())

    def showFavorites(self):
        bundles = self.api.bundle(slugs=self.favorites)

        self.listBundles(bundles, addToFavorites=False)

    def showRecentlyWatched(self):
        videos = list()

        for videoId in self.recentlyWatched:
            video = self.api.programCard(videoId)

            if video is not None:
                videos.append(video)

        if not videos:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013),
                                ADDON.getLocalizedString(30020))
        else:
            self.listVideos(videos)

    def showProgramSeries(self, letter=None):
        self.listBundles(self.api.bundlesWithPublicAsset(letter))

    def listBundles(self, bundle, addToFavorites=True):
        if not bundle:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            if not addToFavorites:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013),
                                    ADDON.getLocalizedString(30018), ADDON.getLocalizedString(30019))
            else:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
        else:
            items = list()
            for programSerie in bundle['Data']:
                if 'ProgramCard' in programSerie and programSerie['ProgramCard']['PrimaryAssetKind'] != 'VideoResource':
                    continue

                infoLabels = {}
                if programSerie['CreatedTime'] is not None:
                    publishTime = self.parseDate(programSerie['CreatedTime'])
                    if publishTime:
                        infoLabels['plotoutline'] = ADDON.getLocalizedString(30004) % publishTime.strftime(
                            '%d. %b %Y kl. %H:%M')
                        infoLabels['date'] = publishTime.strftime('%d.%m.%Y')
                        infoLabels['year'] = int(publishTime.strftime('%Y'))
                        infoLabels['aired'] = publishTime.strftime('%Y-%m-%d')

                infoLabels['title'] = programSerie['Title']

                menuItems = list()

                if self.favorites.count(programSerie['Slug']) > 0:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % programSerie['Slug']
                    menuItems.append((ADDON.getLocalizedString(30201), runScript))
                else:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?addfavorite=%s)" % programSerie['Slug']
                    menuItems.append((ADDON.getLocalizedString(30200), runScript))

                imageAsset = self.api.getAsset('Image', programSerie)
                if imageAsset:
                    iconImage = imageAsset['Uri']
                else:
                    iconImage = ''
                item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage)
                item.setInfo('video', infoLabels)
                item.setProperty('Fanart_Image', FANART_IMAGE)

                item.addContextMenuItems(menuItems, False)

                url = PATH + '?listVideos=' + programSerie['Slug']
                items.append((url, item, True))

            xbmcplugin.addDirectoryItems(HANDLE, items)
            xbmcplugin.setContent(HANDLE, 'tvshows')
            xbmcplugin.endOfDirectory(HANDLE)

    def listAZ(self):
        items = list()

        # All Program Series
        iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png')
        fanartImage = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

        for letter in LETTERS:
            item = xbmcgui.ListItem(letter, iconImage=iconImage)
            item.setProperty('Fanart_Image', fanartImage)

            url = PATH + '?listProgramSeriesByLetter=' + letter
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def searchVideos(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            self.listVideos(self.api.searchProgramCard(keyword))

    def listVideos(self, programCards):
        items = list()
        for programCard in programCards['Data']:
            if 'ProgramCard' in programCard:
                programCard = programCard['ProgramCard']
            if not 'PrimaryAssetUri' in programCard:
                continue

            infoLabels = self.createInfoLabels(programCard)

            imageAsset = self.api.getAsset('Image', programCard)
            if imageAsset:
                iconImage = imageAsset['Uri']
            else:
                iconImage = ''
            item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage)
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', FANART_IMAGE)
            url = PATH + '?videoasset=' + programCard['PrimaryAssetUri']
            item.setProperty('IsPlayable', 'true')
            items.append((url, item))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.setContent(HANDLE, 'episodes')
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def playVideo(self, assetUri):
        self._updateRecentlyWatched(assetUri)
        video = self.api.loadAsset(assetUri)
        if not video:
            raise tvapi.TvNuException('Video with ID %s not found!' % assetUri)

        # if ADDON.getSetting('show.stream.selector') == 'true':
        #     json = self.api._call_api(video['videoResourceUrl'])
        #     options = []
        #     links = sorted(json['links'], key=lambda link: link['bitrateKbps'] if 'bitrateKbps' in link else 0, reverse=True)
        #     for link in links:
        #         options.append('%s (%s kbps)' % (link['linkType'], link['bitrateKbps'] if 'bitrateKbps' in link else '?'))
        #
        #     d = xbmcgui.Dialog()
        #     idx = d.select(video['title'], options)
        #     if idx == -1:
        #         xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        #         return
        #     rtmpUrl = links[idx]['uri']
        #
        # else:
        #     rtmpUrl = self.api._http_request(video['videoManifestUrl'])

        item = xbmcgui.ListItem(path=video)
        xbmcplugin.setResolvedUrl(HANDLE, video is not None, item)

    def parseDate(self, dateString):
        if 'Date(' in dateString:
            try:
                m = re.search('/Date\(([0-9]+).*?\)/', dateString)
                microseconds = long(m.group(1))
                return datetime.datetime.fromtimestamp(microseconds / 1000)
            except ValueError:
                return None
        elif dateString is not None:
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

    def parseTime(self, timeString):
        try:
            m = re.search('([0-9]+):([0-9]+):([0-9]+)(.([0-9]+))?', timeString)
            hours = int(m.group(1))
            minutes = int(m.group(2))
            seconds = int(m.group(3))
            return datetime.datetime(2011, 12, 28, hours, minutes, seconds)
        except ValueError:
            return None

    def parseDuration(self, duration):
        try:
            minutes = int(duration[0:2]) * 60
            minutes += int(duration[3:5])
            minutes += int(duration[6:8]) / 60
            return str(minutes)
        except:
            return 0

    def formatStartTime(self, time):
        startTime = time.hour * 3600
        startTime += time.minute * 60
        startTime += time.second
        return str(startTime * 1000)

    def createInfoLabels(self, programCard):
        infoLabels = dict()

        if programCard['Title'] is not None:
            infoLabels['title'] = programCard['Title']
        else:
            infoLabels['title'] = ADDON.getLocalizedString(30006)

        if 'Description' in programCard and programCard['Description'] is not None:
            infoLabels['plot'] = programCard['Description']

        #if 'duration' in programCard and programCard['duration'] is not None:
        #    infoLabels['duration'] = self.parseDuration(programCard['duration'])
        #if 'broadcastChannel' in programCard and programCard['broadcastChannel'] is not None:
        #    infoLabels['studio'] = programCard['broadcastChannel']
        if 'PrimaryBroadcastStartTime' in programCard and programCard['PrimaryBroadcastStartTime'] is not None:
            broadcastTime = self.parseDate(programCard['PrimaryBroadcastStartTime'])
            if broadcastTime:
                infoLabels['plotoutline'] = ADDON.getLocalizedString(30015) % broadcastTime.strftime(
                    '%d. %b %Y kl. %H:%M')
                infoLabels['date'] = broadcastTime.strftime('%d.%m.%Y')
                infoLabels['aired'] = broadcastTime.strftime('%Y-%m-%d')
                infoLabels['year'] = int(broadcastTime.strftime('%Y'))
        if 'EndPublish' in programCard and programCard['EndPublish'] is not None:
            expireTime = self.parseDate(programCard['EndPublish'])
            if expireTime:
                infoLabels['plot'] += '[CR][CR]' + ADDON.getLocalizedString(30016) % expireTime.strftime(
                    '%d. %b %Y kl. %H:%M')

        return infoLabels

    def addFavorite(self, slug):
        if not self.favorites.count(slug):
            self.favorites.append(slug)
        self._save()

        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30009))

    def delFavorite(self, slug):
        if self.favorites.count(slug):
            self.favorites.remove(slug)
        self._save()
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30010))

    def _updateRecentlyWatched(self, assetUri):
        if self.recentlyWatched.count(assetUri):
            self.recentlyWatched.remove(assetUri)
        self.recentlyWatched.insert(0, assetUri)
        self._save()

    def displayError(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30900)
        line2 = ADDON.getLocalizedString(30901)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

    def displayIOError(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30902)
        line2 = ADDON.getLocalizedString(30903)
        xbmcgui.Dialog().ok(heading, line1, line2, message)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    FAVORITES_PATH = os.path.join(CACHE_PATH, 'favorites.pickle')
    RECENT_PATH = os.path.join(CACHE_PATH, 'recent.pickle')

    FANART_IMAGE = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')


    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    buggalo.addExtraData('cache_path', CACHE_PATH)
    nuAddon = NuAddon()
    try:
        if 'show' in PARAMS:
            if PARAMS['show'][0] == 'allProgramSeries':
                nuAddon.showProgramSeries()
            elif PARAMS['show'][0] == 'listAZ':
                nuAddon.listAZ()
            elif PARAMS['show'][0] == 'mostViewed':
                nuAddon.showMostViewedVideos()
            elif PARAMS['show'][0] == 'search':
                nuAddon.searchVideos()
            elif PARAMS['show'][0] == 'favorites':
                nuAddon.showFavorites()
            elif PARAMS['show'][0] == 'recentlyWatched':
                nuAddon.showRecentlyWatched()

        elif 'listProgramSeriesByLetter' in PARAMS:
            nuAddon.showProgramSeries(letter=PARAMS['listProgramSeriesByLetter'][0])

        elif 'listVideos' in PARAMS:
            nuAddon.showProgramSeriesVideos(PARAMS['listVideos'][0])

        elif 'videoasset' in PARAMS and 'startTime' in PARAMS:
            nuAddon.playVideo(PARAMS['videoId'][0], PARAMS['startTime'][0])

        elif 'videoasset' in PARAMS:
            nuAddon.playVideo(PARAMS['videoasset'][0])

        elif 'addfavorite' in PARAMS:
            nuAddon.addFavorite(PARAMS['addfavorite'][0])

        elif 'delfavorite' in PARAMS:
            nuAddon.delFavorite(PARAMS['delfavorite'][0])

        else:
            nuAddon.showMainMenu()

    except tvapi.TvNuException, ex:
        nuAddon.displayError(str(ex))

    except IOError, ex:
        nuAddon.displayIOError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()

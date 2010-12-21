# DR NU API specs: http://www.dr.dk/nu/api/
import re
import simplejson as json
import datetime
import os
import sys

import xbmc
import xbmcgui
import xbmcplugin

import danishaddons
import danishaddons.web
import danishaddons.info

BASE_API_URL = 'http://www.dr.dk/NU/api/%s'

def getProgramSeries():
    programSeries = json.loads(danishaddons.web.downloadAndCacheUrl(BASE_API_URL % 'programseries', os.path.join(
            danishaddons.ADDON_DATA_PATH, 'programseries.json'), 60))

    iconImage = os.path.join(os.getcwd(), 'icon.png')
    # Latest
    item = xbmcgui.ListItem(danishaddons.msg(30001), iconImage=iconImage)
    xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?newest', item, isFolder=True)
    # Spotlight
    item = xbmcgui.ListItem(danishaddons.msg(30002), iconImage=iconImage)
    xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?spot', item, isFolder=True)
    # Search
    item = xbmcgui.ListItem(danishaddons.msg(30003), iconImage=iconImage)
    xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?search', item, isFolder=True)

    for program in programSeries:
        infoLabels = {}

        if(program['newestVideoPublishTime'] is not None):
            publishTime = parseDate(program['newestVideoPublishTime'])
            infoLabels['plotoutline'] = danishaddons.msg(30004) % publishTime.strftime('%d. %b %Y kl. %H:%M')
            infoLabels['date'] = publishTime.strftime('%d.%m.%Y')
            infoLabels['year'] = int(publishTime.strftime('%Y'))

        infoLabels['title'] = program['title']
        infoLabels['plot'] = program['description']
        infoLabels['count'] = int(program['videoCount'])

        iconImage = BASE_API_URL % ('programseries/' + program['slug'] + '/images/256x256.jpg')
        thumbnailImage = BASE_API_URL % ('programseries/' + program['slug'] + '/images/512x512.jpg')

        item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage, thumbnailImage=thumbnailImage)
        item.setInfo('video', infoLabels)
        url = danishaddons.ADDON_PATH + '?slug=' + program['slug']
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item, isFolder=True)

    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

def searchVideos():
    keyboard = xbmc.Keyboard('', danishaddons.msg(30003))
    keyboard.doModal()
    if(keyboard.isConfirmed()):
        keyword = keyboard.getText()

        videos = json.loads(danishaddons.web.downloadAndCacheUrl(BASE_API_URL % ('videos/all'), os.path.join(
                danishaddons.ADDON_DATA_PATH, 'all.json'), 60))

        for idx in range(len(videos)-1, -1, -1):
            video = videos[idx]
            # simplistic search for title
            if(video['title'].lower().find(keyword.lower()) == -1):
                del videos[idx]

        if(len(videos) == 0):
            xbmcgui.Dialog().ok(danishaddons.msg(30003), danishaddons.msg(30005))
        else:
            listVideos(videos, False)


def listVideos(videos, isSpot):
    for video in videos:
        infoLabels = dict()

        if(video['title'] is not None):
            infoLabels['title'] = video['title']
        else:
            infoLabels['title'] = danishaddons.msg(30006)

        if(isSpot):
            infoLabels['plot'] = video['spotSubTitle']
        else:
            infoLabels['plot'] = video['description']
            if(video.has_key('duration')):
                infoLabels['duration'] = video['duration']
            if(video.has_key('broadcastChannel')):
                infoLabels['studio'] = video['broadcastChannel']
            if(video['broadcastTime'] is not None):
                broadcastTime = parseDate(video['broadcastTime'])
                infoLabels['plotoutline'] = 'Sendt: %s' % broadcastTime.strftime('%d. %b %Y kl. %H:%M')
                infoLabels['date'] = broadcastTime.strftime('%d.%m.%Y')
                infoLabels['aired'] = broadcastTime.strftime('%Y-%m-%d')
                infoLabels['year'] = int(broadcastTime.strftime('%Y'))

        iconImage = BASE_API_URL % ('videos/' + str(video['id']) + '/images/256x256.jpg')
        thumbnailImage = BASE_API_URL % ('videos/' + str(video['id']) + '/images/512x512.jpg')

        item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage, thumbnailImage=thumbnailImage)
        item.setInfo('video', infoLabels)
        item.setProperty('IsPlayable', 'true')
        url = danishaddons.ADDON_PATH + '?id=' + str(video['id'])
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)

    xbmcplugin.addSortMethod(danishaddons.ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)


def playVideo(videoId):
    video = json.loads(danishaddons.web.downloadUrl(BASE_API_URL % ('videos/' + videoId)))

    rtmpUrl = danishaddons.web.downloadUrl(video['videoManifestUrl'])
    if(rtmpUrl[0:7] == '<script'):
        d = xbmcgui.Dialog()
        d.ok(danishaddons.msg(30100), danishaddons.msg(30101), danishaddons.msg(30102))
    else:
        rtmpUrl = rtmpUrl.replace('rtmp://vod.dr.dk/', 'rtmp://vod.dr.dk/cms/')
        item = xbmcgui.ListItem(path = rtmpUrl)
        xbmcplugin.setResolvedUrl(danishaddons.ADDON_HANDLE, True, item)

def parseDate(dateString):
    m = re.search('\/Date\(([0-9]+).*?\)\/', dateString)
    microseconds = long(m.group(1))
    return datetime.datetime.fromtimestamp(microseconds / 1000)


if __name__ == '__main__':
    danishaddons.init(sys.argv)

    if(danishaddons.ADDON_PARAMS.has_key('slug')):
        videos = json.loads(danishaddons.web.downloadAndCacheUrl(BASE_API_URL % 'programseries/' + danishaddons.ADDON_PARAMS['slug'] + '/videos',
            os.path.join(danishaddons.ADDON_DATA_PATH, 'programseries-%s.json' % danishaddons.ADDON_PARAMS['slug']), 60))
        listVideos(videos, False)

    elif(danishaddons.ADDON_PARAMS.has_key('newest')):
        videos = json.loads(danishaddons.web.downloadAndCacheUrl(BASE_API_URL % 'videos/newest', os.path.join(
                danishaddons.ADDON_DATA_PATH, 'newest.json'), 60))
        listVideos(videos, False)

    elif(danishaddons.ADDON_PARAMS.has_key('spot')):
        videos = json.loads(danishaddons.web.downloadAndCacheUrl(BASE_API_URL % 'videos/spot', os.path.join(
                danishaddons.ADDON_DATA_PATH, 'spot.json'), 60))
        listVideos(videos, True)

    elif(danishaddons.ADDON_PARAMS.has_key('search')):
        searchVideos()

    elif(danishaddons.ADDON_PARAMS.has_key('id')):
        playVideo(danishaddons.ADDON_PARAMS['id'])

    else:
        getProgramSeries()


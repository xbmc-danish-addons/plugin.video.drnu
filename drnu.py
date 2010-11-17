# DR NU API specs: http://www.dr.dk/nu/api/
import xbmc
import xbmcgui
import xbmcplugin
import re
import sys
import urllib
import simplejson as json
import time
import datetime
from danishaddons import *

BASE_API_URL = 'http://www.dr.dk/NU/api/%s'

def getProgramSeries():
	programSeries = json.loads(web.downloadUrl(BASE_API_URL % 'programseries'))

	item = xbmcgui.ListItem('Nyeste')
	xbmcplugin.addDirectoryItem(ADDON_HANDLE, ADDON_PATH + '?newest', item, isFolder=True)
	item = xbmcgui.ListItem('Spotlight')
	xbmcplugin.addDirectoryItem(ADDON_HANDLE, ADDON_PATH + '?spot', item, isFolder=True)
	item = xbmcgui.ListItem('Søg')
	xbmcplugin.addDirectoryItem(ADDON_HANDLE, ADDON_PATH + '?search', item, isFolder=True)


	for program in programSeries:
		infoLabels = {}

		if(program['newestVideoPublishTime'] != None):
			publishTime = parseDate(program['newestVideoPublishTime'])
			infoLabels['plotoutline'] = 'Nyeste udsendelse: %s' % publishTime.strftime('%d. %b %Y kl. %H:%M')
			infoLabels['date'] = publishTime.strftime('%d.%m.%Y')
			infoLabels['year'] = int(publishTime.strftime('%Y'))

		infoLabels['title'] = program['title']
		infoLabels['plot'] = program['description']
		infoLabels['count'] = int(program['videoCount'])

		iconImage = BASE_API_URL % ('programseries/' + program['slug'] + '/images/256x256.jpg')
		thumbnailImage = BASE_API_URL % ('programseries/' + program['slug'] + '/images/512x512.jpg')

		item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage, thumbnailImage=thumbnailImage)
		item.setInfo('video', infoLabels)
		url = ADDON_PATH + '?slug=' + program['slug']
		xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, item, isFolder=True)

	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def searchVideos():
	keyboard = xbmc.Keyboard('', 'Søg')
	keyboard.doModal()
	if(keyboard.isConfirmed()):
		keyword = keyboard.getText()

		videos = json.loads(web.downloadUrl(BASE_API_URL % ('videos/all')))

		for idx in range(len(videos)-1, -1, -1):
			video = videos[idx]
			# simplistic search for title
			if(video['title'].lower().find(keyword.lower()) == -1):
				del videos[idx]

		if(len(videos) == 0):
			print "no results"
		else:
			listVideos(videos, False)
		

def listVideos(videos, isSpot):
	for video in videos:
		infoLabels = {}

		if(video['title'] != None):
			infoLabels['title'] = video['title']
		else:
			infoLabels['title'] = 'Ukendt titel'

		if(isSpot):
			infoLabels['plot'] = video['spotSubTitle']
		else:
			infoLabels['plot'] = video['description']
			if(video.has_key('duration')):
				infoLabels['duration'] = video['duration']
			if(video.has_key('broadcastChannel')):
				infoLabels['studio'] = video['broadcastChannel']
			if(video['broadcastTime'] != None):
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
		url = ADDON_PATH + '?id=' + str(video['id'])
		xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, item)

	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)


def playVideo(videoId):
	video = json.loads(web.downloadUrl(BASE_API_URL % ('videos/' + videoId)))

	rtmpUrl = web.downloadUrl(video['videoManifestUrl'])
	rtmpUrl = rtmpUrl.replace('rtmp://vod.dr.dk/', 'rtmp://vod.dr.dk/cms/')

	item = xbmcgui.ListItem(path = rtmpUrl)
	xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, item)

def parseDate(dateString):
	m = re.search('\/Date\(([0-9]+).*?\)\/', dateString)
	microseconds = long(m.group(1))
	return datetime.datetime.fromtimestamp(microseconds / 1000)




if(ADDON_PARAMS.has_key('slug')):
	videos = json.loads(web.downloadUrl(BASE_API_URL % 'programseries/' + ADDON_PARAMS['slug'] + '/videos'))
	listVideos(videos, False)

elif(ADDON_PARAMS.has_key('newest')):
	videos = json.loads(web.downloadUrl(BASE_API_URL % 'videos/newest'))
	listVideos(videos, False)

elif(ADDON_PARAMS.has_key('spot')):
	videos = json.loads(web.downloadUrl(BASE_API_URL % 'videos/spot'))
	listVideos(videos, True)

elif(ADDON_PARAMS.has_key('search')):
	searchVideos()

elif(ADDON_PARAMS.has_key('id')):
	playVideo(ADDON_PARAMS['id'])

else:
	getProgramSeries()


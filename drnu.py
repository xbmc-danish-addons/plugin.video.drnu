import xbmc
import xbmcgui
import xbmcplugin
import sys
import urllib
import simplejson as json
import time
import datetime
from danishaddons import *

class DRNUPlayer:
  def __init__(self):
    pass
    
  def CreateDirectoryItem(self, folder=False, items=None):
    if(folder):
      self.folder = folder
      for item in items.keys():
        self.title = unicode(items[item][0]).encode('utf-8')
        self.description = unicode(items[item][1]).encode('utf-8')
        self.newestVideoId = int(items[item][2])
        self.newestVideoPublishTime = items[item][3]
        self.videoCount = int(items[item][4])
        self.thumbnailImage = items[item][5]
        self.listitem = xbmcgui.ListItem(label=self.title, thumbnailImage=(self.thumbnailImage))
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url=ADDON_PATH + '?' + item, listitem=self.listitem, isFolder=self.folder, totalItems=len(items))
      xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
      xbmcplugin.endOfDirectory(ADDON_HANDLE)
    else:
      self.folder = folder
      for item in items.keys():
        self.description = unicode(items[item][0]).encode('utf-8')
        self.title = unicode(items[item][1]).encode('utf-8')
        self.duration = items[item][2]
        self.broadcastTime = items[item][3]
        self.broadcastChannel = items[item][4]
        self.videoManifestUrl = items[item][5]
        self.isPremiere = items[item][6]
        self.formattedBroadcastTime = items[item][7]
        self.videoURL = items[item][8]
        if(self.videoURL.startswith('<script>self.resizeTo')):
          break
        if(self.videoURL[:4] == 'rtmp'):
          self.videoURL = self.videoURL.replace('rtmp://vod.dr.dk/', 'rtmp://vod.dr.dk/cms/')
        self.thumbnailImage = 'http://www.dr.dk/NU/api/videos/' + str(item) + '/images/250x250.jpg'
        if(self.broadcastTime):
          self.broadcastTime = datetime.datetime.fromtimestamp(float(items[item][3][6:-10])).strftime('%Y.%m.%d')
          self.date = datetime.datetime.fromtimestamp(float(items[item][3][6:-10])).strftime('%d.%m.%Y')
        else:
          self.broadcastTime = datetime.datetime.now().strftime('%Y.%m.%d')
          self.date = datetime.datetime.now().strftime('%d.%m.%Y')
        if not(self.broadcastChannel):
          self.broadcastChannel = 'Unknown'

        self.listitem = xbmcgui.ListItem(label=self.title, thumbnailImage=(self.thumbnailImage))
        self.listitem.setInfo(type='video', infoLabels={
                                                        'plot' : self.description,
                                                        'duration' : self.duration,
                                                        'studio' : self.broadcastChannel,
                                                        'aired' : self.broadcastTime,
                                                        'date' : self.date,
                                                       })
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url=self.videoURL, listitem=self.listitem, isFolder=self.folder, totalItems=len(items))
      xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATE)
      xbmcplugin.endOfDirectory(ADDON_HANDLE)

  def getVideos(self, slug):
    self.url = 'http://www.dr.dk/NU/api/programseries/' + slug  + '/videos'
    self.result = json.load(urllib.urlopen(self.url))

    # id : [description, title, duration, broadcastTime, broadcastChannel, videoManifestUrl, isPremiere, formattedBroadcastTime]
    self.videos = {}
    
    for video in self.result:
      self.videos[video['id']] = [video['description'], video['title'], video['duration'],\
             video['broadcastTime'], video['broadcastChannel'], video['videoManifestUrl'],\
             video['isPremiere'], video['formattedBroadcastTime']]
      if(video['videoManifestUrl'][:4] == 'http'):
        videoURL = urllib.urlopen(video['videoManifestUrl']).read()
      else:
        videoURL = urllib.urlopen('http://www.dr.dk' + video['videoManifestUrl']).read()
      self.videos[video['id']].append(videoURL)
    return self.videos

  def getProgramSeries(self):
    url = 'http://www.dr.dk/NU/api/programseries'
    result = json.load(urllib.urlopen(url))

    #slug : [title, description, newestVideoId, newestVideoPublishTime, videoCount, thumbnailImage]
    programSeries = {}

    for programSerie in result:
      programSeries[programSerie['slug']] = [programSerie['title'], programSerie['description'],\
                    programSerie['newestVideoId'], programSerie['newestVideoPublishTime'], programSerie['videoCount']]

    for k in programSeries.keys():
      programSeries[k][3] = datetime.datetime.fromtimestamp(float(programSeries[k][3][6:-10]))
      programSeries[k].append(url + '/' + k + '/images/250x250.jpg')
    return programSeries
  
MyPlayer = DRNUPlayer()
if(sys.argv[2][:1] == '?'):
  MyPlayer.CreateDirectoryItem(folder=False, items=MyPlayer.getVideos(sys.argv[2][1:]))
  
else:
  MyPlayer.CreateDirectoryItem(folder=True, items=MyPlayer.getProgramSeries())


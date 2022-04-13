import json
from tvapi import Api
from pathlib import Path
import sys
import time

cachepath = Path('.').resolve()


def tr(id, da=True):
    msgid = str(id)
    msgstr = str(id)

    if id == 30506:
        msgid = "Hard-of-hearing"
        msgstr = "For hørehæmmede"

    if id == 30507:
        msgid = "Subtitles"
        msgstr = "Undertekster"

    if id == 30508:
        msgid = "empty"
        msgstr = "Ingen undertekster"

    if da:
        return msgstr
    else:
        return msgid


api = Api(cachepath, tr)
api2 = NewApi()

#print(api2.user_token())

#print(api2.search('vera'))

#print(api2.get_stream(302445))

spotlight = api.getSelectedList()
for item in spotlight:
    print(item['Title'], item['Slug'])
    print(json.dumps(item, indent=2))
#    info = {
#        'image': item['PrimaryImageUri'],
#        'plot': item['Description'],
#        'time': item['PrimaryBroadcastStartTime']
#    }
#    print(info)
    print()

#api.recache_requests(cache_urls=False, cache_episodes=True, clear_expired=False, verbose=True)
sys.exit(0)

#series = api.searchSeries('abdel')[0]
#episodes = api.getEpisodes(series['SeriesSlug'])
# print(json.dumps(episodes, indent=2))
# url = episodes[0]['PrimaryAsset']['Uri']
# video = api.getVideoUrl(url)
idxs = api.getProgramIndexes()
AZidxs = api.getAZIndexes()
for idx, AZidx in zip(idxs, AZidxs):
    d = {k: idx[k] for k in idx if k in ['Title', '_Param']}
#    print(d)
    print(idx['_Param'])
    assert(d == AZidx)
    series = api.searchSeries(idx['_Param'], startswith=True)
    if len(series) != idx['TotalSize']:
        print(len(series), idx['TotalSize'])
    assert(abs(len(series) - idx['TotalSize']) <= 3)

sys.exit(0)

series = api.searchSeries('deadline')[0]
keys = ['Type', 'SeriesTitle', 'SeriesSlug', 'SeriesUrn', 'SeasonEpisodeNumberingValid', 'SeasonTitle', 'SeasonSlug', 'SeasonUrn', 'SeasonNumber', 'PrimaryChannel', 'PrimaryChannelSlug', 'PrePremiere', 'ExpiresSoon', 'OnlineGenreText',
        'PrimaryAsset', 'HasPublicPrimaryAsset', 'AssetTargetTypes', 'PrimaryBroadcastDay', 'PrimaryBroadcastStartTime', 'SortDateTime', 'Slug', 'Urn', 'PrimaryImageUri', 'PresentationUri', 'PresentationUriAutoplay', 'AgeClassification', 'Title']
assert(list(series.keys()) == keys)

keys = ['Description', 'ProductionNumber', 'ProductionCountry', 'ProductionYear', 'Site', 'ChannelType', 'PrimaryBroadcast', 'Chapters', 'Type', 'SeriesTitle', 'SeriesSlug', 'SeriesUrn', 'SeasonEpisodeNumberingValid', 'SeasonTitle', 'SeasonSlug', 'SeasonUrn', 'SeasonNumber', 'PrimaryChannel',
        'PrimaryChannelSlug', 'PrePremiere', 'ExpiresSoon', 'OnlineGenreText', 'PrimaryAsset', 'HasPublicPrimaryAsset', 'AssetTargetTypes', 'PrimaryBroadcastStartTime', 'SortDateTime', 'Slug', 'Urn', 'PrimaryImageUri', 'PresentationUri', 'PresentationUriAutoplay', 'AgeClassification', 'Title']
episodes = api.getEpisodes(series['SeriesSlug'])
assert(list(episodes[0].keys()) == keys and len(episodes) > 5)
#    print(episodes[0].keys(), len(episodes))

themes = api.getThemes()
print('themes', len(themes))

latest = api.getLatestPrograms(channel='')
print('latest', len(latest))

most = api.getMostViewed()
print('most', len(most))

res = api.searchSeries('bonderøven')
assert(len(res) >= 1)
#    print(res)

minisjang = api.getChildrenFrontItems('dr-minisjang')
episodes = api.getEpisodes(minisjang[0]['SeriesSlug'])
url = episodes[0]['PrimaryAsset']['Uri']
video = api.getVideoUrl(url)
print(url, len(episodes))
print(video['Uri'])

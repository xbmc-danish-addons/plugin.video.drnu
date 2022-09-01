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
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import hashlib
import json
from pathlib import Path
import pickle
import requests
import requests_cache
import time
from dateutil import parser
from datetime import datetime, timezone, timedelta


CHANNEL_IDS = [20875, 20876, 192099, 192100, 20892]


class Api():
    def __init__(self, cachePath, getLocalizedString, expire_hours=24):
        self.cachePath = cachePath
        self.tr = getLocalizedString

        # cache expires after: 3600 = 1hour
        self.init_sqlite_db(expire_hours)

        # we need to have something in the srt to make kodi use it
        self.empty_srt = f'{self.cachePath}/{self.tr(30508)}.da.srt'
        Path(self.empty_srt).write_text('1\n00:00:00,000 --> 00:01:01,000\n')

        self.token_file = Path(f'{self.cachePath}/token.json')
        self._user_token = None
        self.refresh_tokens()

    def init_sqlite_db(self, expire_hours):
        request_fname = str(self.cachePath/'requests.cache')
        self.session = requests_cache.CachedSession(request_fname, backend='sqlite', expire_after=3600*expire_hours)

        if (self.cachePath/'request_cleaned').exists():
            if (time.time() - (self.cachePath/'request_cleaned').stat().st_mtime)/3600/24 < 7:
                # less than 7 days since last cleaning, no need...
                return
        try:
            self.session.remove_expired_responses()
        except Exception:
            if (self.cachePath/'requests.cache.sqlite').exists():
                (self.cachePath/'requests.cache.sqlite').unlink()
            self.session = requests_cache.CachedSession(request_fname, backend='sqlite', expire_after=3600*expire_hours)
        (self.cachePath/'request_cleaned').write_text('')

    def deviceid(self):
        v = int(Path(__file__).stat().st_mtime)
        h = hashlib.md5(str(v).encode('utf-8')).hexdigest()
        return '-'.join([h[:8], h[8:12], h[12:16], h[16:20], h[20:32]])

    def read_token(self, s):
        tokens = json.loads(s)
        time_struct = time.strptime(tokens[0]['expirationDate'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        self._token_expire = datetime(*time_struct[0:6])
        self._user_token = tokens[0]['value']
        self._profile_token = tokens[1]['value']

    def request_tokens(self):
        data = {"deviceId": self.deviceid(), "scopes": ["Catalog"], "optout": False}
        params = {'device': 'web_browser', 'ff': 'idp,ldp,rpt', 'lang': 'da', 'supportFallbackToken': True}

        url = 'https://production.dr-massive.com/api/authorization/anonymous-sso?'
        u = requests.post(url, json=data, params=params)
        self._user_token = None
        if u.status_code == 200:
            self.token_file.write_bytes(u.content)
            self.read_token(u.content)
        else:
            print(u.text)
            raise ApiException(f'Failed to get new token from: {url}')

    def refresh_tokens(self):
        if self._user_token is None:
            if self.token_file.exists():
                self.read_token(self.token_file.read_bytes())
            else:
                self.request_tokens()
        if (self._token_expire - datetime.now()).total_seconds() < 120:
            self.request_tokens()

    def user_token(self):
        self.refresh_tokens()
        return self._user_token

    def profile_token(self):
        self.refresh_tokens()
        return self._profile_token

    def get_programcard(self, path, data=None):
        url = 'https://www.dr-massive.com/api/page?'
        if data is None:
            data = {
                'item_detail_expand': 'all',
                'list_page_size': '24',
                'max_list_prefetch': '3',
                'path': path
            }
        u = requests.get(url, params=data)
        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def search(self, term):
        url = 'https://production.dr-massive.com/api/search'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        data = {
            'item_detail_expand': 'all',
            'list_page_size': '24',
            'group': 'true',
            'term': term
        }
        u = self.session.get(url, params=data, headers=headers)
        if u.status_code == 200:
            return u.json()
        else:
            print(u.text)
            raise ApiException(u.text)

    def get_home(self):
        data = dict(
            list_page_size=24,
            max_list_prefetch=3,
            item_detail_expand='all',
            path='/',
            segments='drtv,mt_K8q4Nz3,optedin',
        )
        js = self.get_programcard('/', data=data)
        items = [{'title': 'Programmer A-Å', 'path': '/a-aa', 'icon': 'all.png'}]
        for item in js['entries']:
            if item['title'] not in ['', 'Se Live TV']:
                items.append({'title': item['title'], 'path': item['list']['path']})
        return items

    def getLiveTV(self):
        channels = []
        schedules = self.get_channel_schedule_strings()
        for id in CHANNEL_IDS:
            card = self.get_programcard(f'/kanal/{id}')
            card['entries'][0]['schedule_str'] = schedules[id]
            channels += card['entries']
        return channels

    def get_children_front_items(self, channel):
        names = {
            'dr-ramasjang': '/ramasjang_a-aa',
            'dr-minisjang': '/minisjang/a-aa'
            }
        name = names[channel]
        js = self.get_programcard(name)
        items = []
        for item in js['entries']:
            if item['type'] == 'ListEntry':
                if channel == 'dr-ramasjang':
                    url = name + '/' + item['list']['parameter'].split(':')[1]
                    local_js = self.get_programcard(url)
                    items += local_js['entries'][0]['list']['items']
                else:
                    items += item['list']['items']
        return items

    def get_stream(self, id):
        url = f'https://production.dr-massive.com/api/account/items/{int(id)}/videos?'
        headers = {"X-Authorization": f'Bearer {self.user_token()}'}
        data = {
            'delivery': 'stream',
            'device': 'web_browser',
            'ff': 'idp,ldp,rpt',
            'lang': 'da',
            'resolution': 'HD-1080',
            'sub': 'Anonymous'
        }

        u = self.session.get(url, params=data, headers=headers)
        if u.status_code == 200:
            for stream in u.json():
                if stream['accessService'] == 'StandardVideo':
                    return stream
            return None
        else:
            raise ApiException(u.text)

    def getVideoUrl(self, id):
        stream = self.get_stream(id)
        url = stream['url']
        subtitlesUri = None
        return {
            'url': url,
            'SubtitlesUri': subtitlesUri
        }

    def get_info(self, item):
        title = item['title']
        if item['type'] == 'season':
            title += f" {item['seasonNumber']}"
        elif item.get('contextualTitle', None):
            cont = item['contextualTitle']
            if cont.count('.') >= 1 and cont.split('.', 1)[1].strip() not in title:
                title += f" ({item['contextualTitle']})"

        infoLabels = {'title': title}
        if item.get('shortDescription', ''):
            infoLabels['plot'] = item['shortDescription']
        if item.get('tagline', ''):
            infoLabels['plotoutline'] = item['tagline']
        if item.get('customFields'):
            if item['customFields'].get('BroadcastTimeDK'):
                broadcast = parser.parse(item['customFields']['BroadcastTimeDK'])
                infoLabels['date'] = broadcast.strftime('%d.%m.%Y')
                infoLabels['aired'] = broadcast.strftime('%Y-%m-%d')
                infoLabels['year'] = int(broadcast.strftime('%Y'))
        if item.get('seasonNumber'):
            infoLabels['season'] = item['seasonNumber']
        if item['type'] in ["movie", "season", "episode"]:
            infoLabels['mediatype'] = item['type']
        elif item['type'] == 'program':
            infoLabels['mediatype'] = 'tvshow'
        return title, infoLabels

    def get_schedules(self, channels=CHANNEL_IDS, date=None, hour=None):
        url = 'https://production-cdn.dr-massive.com/api/schedules?'
        now = datetime.now()
        if date is None:
            date = now.strftime("%Y-%m-%d")
        if hour is None:
            hour = int(now.strftime("%H"))
        data = {
            'date': date,
            'hour': hour-2,
            'duration': 6,
            'channels': channels,
        }
        u = requests.get(url, params=data)
        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def get_channel_schedule_strings(self, channels=CHANNEL_IDS):
        out = {}
        now = datetime.now(timezone.utc)
        for channel in self.get_schedules():
            id = int(channel['channelId'])
            out[id] = ''
            for item in channel['schedules']:
                if parser.parse(item['endDate']) > now and out[id].count('\n') < 5:
                    t = parser.parse(item['startDate']) + timedelta(hours=2)
                    start = t.strftime('%H:%M')
                    out[id] += f"{start} {item['item']['title']} \n"
        return out


class ApiException(Exception):
    pass

# -*- coding: utf-8 -*-
"""Integration tests for Routing functionality"""

from pathlib import Path
import json
import sys
import urllib.parse as urlparse

xbmc = __import__('xbmc')
xbmcaddon = __import__('xbmcaddon')
xbmcgui = __import__('xbmcgui')
xbmcplugin = __import__('xbmcplugin')
xbmcvfs = __import__('xbmcvfs')
inputstreamhelper = __import__('inputstreamhelper')

plugin_url = 'plugin://plugin.video.drnu/'

basedir = Path(__file__).parent.parent
sys.path.insert(0, str((basedir).resolve()))
from resources.lib import addon

userdata = Path(addon.translatePath(addon.addon.getAddonInfo('profile')))

menudata = (userdata/'menudata')
menudata.mkdir(parents=True, exist_ok=True)

addon.tvapi.cache_path = lambda path: True
handle = addon.DrDkTvAddon(plugin_url=plugin_url, plugin_handle=1)
handle._plugin_handle = {}

main_menu_js = json.loads((menudata/'main_menu.json').read_text())

UPDATE_TESTS = False
UPDATE_CACHE = False

def get_items():
    new_items = handle._plugin_handle.copy()
    handle._plugin_handle = {}
    return new_items


def iteminfo(item):
    url = item.url.replace(plugin_url, '')
    return {
            'label': item.label,
            'url': url,
            'params': dict(urlparse.parse_qsl(url[1:])),
            'info': vars(item.infotag),
            'properties': item.properties,
            'contextmenu': [list(c) for c in item.context_menu]
        }


def item_from_label(items, label):
    for item in items:
        if item['label'] == label:
            return item
    return {}


def request_get(url, params=None, headers=None, use_cache=True):
    u = handle.api.session.get(url, params=params, headers=headers, timeout=addon.tvapi.GET_TIMEOUT)
    if UPDATE_CACHE is False:
        assert u.from_cache
    assert u.status_code == 200
    return u.json()

handle.api._request_get = request_get


def myEqual(arg1, arg2):
    if UPDATE_TESTS and arg1 != arg2:
        print(arg1, arg2)
    assert arg1 == arg2


def test_basemenus(capsys):
    with capsys.disabled():
        handle._plugin_handle = {}
        main_menu = []
        handle.showMainMenu('drtv')
        for label, item in get_items().items():
            main_menu.append(iteminfo(item))
        if UPDATE_TESTS:
            (menudata/'main_menu.json').write_text(json.dumps(main_menu, indent=2, ensure_ascii=False))
        assert json.loads((menudata/'main_menu.json').read_text()) == main_menu

        handle.route(main_menu[2]['url'])
        myEqual(main_menu[2]['label'], 'Daglige forslag')
        menu = []
        for label, item in get_items().items():
            menu.append(iteminfo(item))
        if UPDATE_TESTS:
            (menudata/'daglige_forslag.json').write_text(json.dumps(menu, indent=2, ensure_ascii=False))
        assert json.loads((menudata/'daglige_forslag.json').read_text()) == menu

        handle.route(main_menu[3]['url'])
        myEqual(main_menu[3]['label'], 'De største programmer lige nu')
        menu = []
        for label, item in get_items().items():
            menu.append(iteminfo(item))
        if UPDATE_TESTS:
            (menudata/'største_programmer.json').write_text(json.dumps(menu, indent=2, ensure_ascii=False))
        assert json.loads((menudata/'største_programmer.json').read_text()) == menu

def test_ramasjang(capsys):
    with capsys.disabled():
        handle.route('?area=ramasjang')
        a_aa = [iteminfo(item) for item in get_items().values()]
        bluey = item_from_label(a_aa, 'Bluey')
        addon.addon.settings['disable.kids.seasons'] = 'true'
        handle.route(bluey['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
        myEqual(len(episodes), 12)

        addon.addon.settings['disable.kids.seasons'] = 'false'
        handle.route(bluey['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
        myEqual(len(episodes), 12)

        addon.addon.settings['disable.kids.menu'] = 'false'
        handle.route('?area=ramasjang')
        home_items = [iteminfo(item) for item in get_items().values()]
        from_home = item_from_label(home_items, 'Skab med Ramasjang')
        handle.route(from_home['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
        myEqual(len(episodes), 5)




def test_gensyn(capsys):
    with capsys.disabled():
        handle.route('?area=gensyn')
        items = [iteminfo(item) for item in get_items().values()]
#        print(items[1])

        # Årtier
        handle.route(items[5]['url'])
        items2 = [iteminfo(item) for item in get_items().values()]
#        print(items2[4])

        # 1990'erne
        handle.route(items2[4]['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
#        print(episodes[1])
        assert episodes[1]['info']['title'] == 'Casper & Mandrilaftalen 1'


def test_a_aa(capsys):
    with capsys.disabled():
        # A - AA
        handle._plugin_handle = {}
        handle.route(main_menu_js[1]['url'])
        a_aa = [iteminfo(item) for item in get_items().values()]
        assert len(a_aa) > 27
        assert a_aa[0]['label'] == 'A'

        handle.route(a_aa[0]['url'])
        a = [iteminfo(item) for item in get_items().values()]
        myEqual(len(a), 116)

        myEqual(a[0]['label'], 'A Storm Foretold - det amerikanske oprør')
#        handle.route(a[0]['url']) # test playing


def test_search(capsys):
    with capsys.disabled():
        handle._plugin_handle = {}
        handle.search()
        res = [iteminfo(item) for item in get_items().values()]
        myEqual(res[0]['label'], 'Series (14 found)')

        handle._plugin_handle = {}
        handle.route(res[0]['url'])
        res = [iteminfo(item) for item in get_items().values()]
        myEqual(len(res), 14)

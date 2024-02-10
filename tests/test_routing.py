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
if (userdata/'favorites6.pickle').exists():
    (userdata/'favorites6.pickle').unlink()

menudata = (userdata/'menudata')
menudata.mkdir(parents=True, exist_ok=True)

addon.tvapi.cache_path = lambda path: True
handle = addon.DrDkTvAddon(plugin_url=plugin_url, plugin_handle=1)
handle._plugin_handle = {}

main_menu_js = json.loads((menudata/'main_menu.json').read_text())

UPDATE_TESTS = False


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
            'info': item.info,
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
    if UPDATE_TESTS is False:
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
        handle.showMainMenu()
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
        handle.route('?area=3')
        a_aa = [iteminfo(item) for item in get_items().values()]
        bluey = item_from_label(a_aa, 'Bluey')
        addon.addon.settings['disable.kids.seasons'] = 'true'
        handle.route(bluey['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
        myEqual(len(episodes), 12)

        addon.addon.settings['disable.kids.seasons'] = 'false'
        handle.route(bluey['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
        myEqual(len(episodes), 2)

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
        myEqual(len(a), 96)

        myEqual(a[0]['label'], 'A Very English Scandal')
        handle.route(a[0]['url'])


def test_search(capsys):
    with capsys.disabled():
        handle._plugin_handle = {}
        handle.search()
        res = [iteminfo(item) for item in get_items().values()]
        myEqual(res[0]['label'], 'Series (13 found)')

        handle.route(res[0]['url'])
        res = [iteminfo(item) for item in get_items().values()]
        myEqual(len(res), 13)


def test_pickles(capsys):
    with capsys.disabled():
        handle._plugin_handle = {}
        handle.route('?show=favorites')
        res = [iteminfo(item) for item in get_items().values()]
        myEqual(res, [])
        myEqual(handle.favorites, {})

        handle.route(main_menu_js[3]['url'])
        biggest_shows = [iteminfo(item) for item in get_items().values()]
        shows = [s for s in biggest_shows if len(s['contextmenu']) == 2] # we only have this option for series

        # add first show to favourit pickle
        fav0 = shows[0]['contextmenu'][1]
        myEqual(fav0[0], '30009')
        handle.route(fav0[1].replace('RunPlugin(plugin://plugin.video.drnu/', '')[:-1])

        # add second show to favourit pickle
        fav1 = shows[1]['contextmenu'][1]
        myEqual(fav1[0], '30009')
        handle.route(fav1[1].replace('RunPlugin(plugin://plugin.video.drnu/', '')[:-1])

        handle.route('?show=favorites')
        res = [iteminfo(item) for item in get_items().values()]
        myEqual(len(res), 2)
        myEqual(len(handle.favorites), 2)

        # update contextmenus
        handle.route(main_menu_js[3]['url'])
        biggest_shows = [iteminfo(item) for item in get_items().values()]
        shows = [s for s in biggest_shows if len(s['contextmenu']) == 2]

        # check we now have delete context menu
        fav0 = shows[0]['contextmenu'][1]
        myEqual(fav0[0], '30010')
        handle.route(fav0[1].replace('RunPlugin(plugin://plugin.video.drnu/', '')[:-1])

        handle.route('?show=favorites')
        res = [iteminfo(item) for item in get_items().values()]
        myEqual(len(res), 1)
        myEqual(len(handle.favorites), 1)
        myEqual(list(handle.favorites.keys())[0], shows[1]['label'])
        myEqual(res[0]['label'], shows[1]['label'])

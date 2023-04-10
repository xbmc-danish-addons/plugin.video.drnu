# -*- coding: utf-8 -*-
"""Integration tests for Routing functionality"""

from pathlib import Path
import unittest
import json

from resources.lib import addon
import urllib.parse as urlparse

xbmc = __import__('xbmc')
xbmcaddon = __import__('xbmcaddon')
xbmcgui = __import__('xbmcgui')
xbmcplugin = __import__('xbmcplugin')
xbmcvfs = __import__('xbmcvfs')
inputstreamhelper = __import__('inputstreamhelper')

plugin_url = 'plugin://plugin.video.drnu/'

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


class TestOffline(unittest.TestCase):

    def myEqual(self, arg1, arg2):
        if UPDATE_TESTS and arg1 != arg2:
            print(arg1, arg2)
        self.assertEqual(arg1, arg2)

    def test_basemenus(self):
        handle._plugin_handle = {}
        main_menu = []
        handle.showMainMenu()
        for label, item in get_items().items():
            main_menu.append(iteminfo(item))
        if UPDATE_TESTS:
            (menudata/'main_menu.json').write_text(json.dumps(main_menu, indent=2, ensure_ascii=False))
        self.assertEqual(json.loads((menudata/'main_menu.json').read_text()), main_menu)

        handle.route(main_menu[2]['url'])
        self.myEqual(main_menu[2]['label'], 'Daglige forslag')
        menu = []
        for label, item in get_items().items():
            menu.append(iteminfo(item))
        if UPDATE_TESTS:
            (menudata/'daglige_forslag.json').write_text(json.dumps(menu, indent=2, ensure_ascii=False))
        self.assertEqual(json.loads((menudata/'daglige_forslag.json').read_text()), menu)

        handle.route(main_menu[3]['url'])
        self.myEqual(main_menu[3]['label'], 'De største programmer lige nu')
        menu = []
        for label, item in get_items().items():
            menu.append(iteminfo(item))
        if UPDATE_TESTS:
            (menudata/'største_programmer.json').write_text(json.dumps(menu, indent=2, ensure_ascii=False))
        self.assertEqual(json.loads((menudata/'største_programmer.json').read_text()), menu)

    def test_ramasjang(self):
        handle.route('?area=3')
        a_aa = [iteminfo(item) for item in get_items().values()]
        bluey = item_from_label(a_aa, 'Bluey')
        addon.addon.settings['disable.kids.seasons'] = 'true'
        handle.route(bluey['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(episodes), 12)

        addon.addon.settings['disable.kids.seasons'] = 'false'
        handle.route(bluey['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(episodes), 2)

    def test_a_aa(self):
        # A - AA
        handle._plugin_handle = {}
        handle.route(main_menu_js[1]['url'])
        a_aa = [iteminfo(item) for item in get_items().values()]
        self.assertTrue(len(a_aa) > 27)
        self.assertTrue(a_aa[0]['label'] == 'A')

        handle.route(a_aa[0]['url'])
        a = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(a), 96)

        self.myEqual(a[0]['label'], 'A Very English Scandal')
        handle.route(a[0]['url'])

    def test_search(self):
        handle._plugin_handle = {}
        handle.search()
        res = [iteminfo(item) for item in get_items().values()]
        self.myEqual(res[0]['label'], 'Series (13 found)')

        handle.route(res[0]['url'])
        res = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(res), 13)

    def test_pickles(self):
        handle._plugin_handle = {}
        handle.route('?show=favorites')
        res = [iteminfo(item) for item in get_items().values()]
        self.myEqual(res, [])
        self.myEqual(handle.favorites, {})

        handle.route(main_menu_js[3]['url'])
        biggest_shows = [iteminfo(item) for item in get_items().values()]
        shows = [s for s in biggest_shows if len(s['contextmenu']) == 2] # we only have this option for series

        # add first show to favourit pickle
        fav0 = shows[0]['contextmenu'][1]
        self.myEqual(fav0[0], '30009')
        handle.route(fav0[1].replace('RunPlugin(plugin://plugin.video.drnu/', '')[:-1])

        # add second show to favourit pickle
        fav1 = shows[1]['contextmenu'][1]
        self.myEqual(fav1[0], '30009')
        handle.route(fav1[1].replace('RunPlugin(plugin://plugin.video.drnu/', '')[:-1])

        handle.route('?show=favorites')
        res = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(res), 2)
        self.myEqual(len(handle.favorites), 2)

        # update contextmenus
        handle.route(main_menu_js[3]['url'])
        biggest_shows = [iteminfo(item) for item in get_items().values()]
        shows = [s for s in biggest_shows if len(s['contextmenu']) == 2]

        # check we now have delete context menu
        fav0 = shows[0]['contextmenu'][1]
        self.myEqual(fav0[0], '30010')
        handle.route(fav0[1].replace('RunPlugin(plugin://plugin.video.drnu/', '')[:-1])

        handle.route('?show=favorites')
        res = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(res), 1)
        self.myEqual(len(handle.favorites), 1)
        self.myEqual(list(handle.favorites.keys())[0], shows[1]['label'])
        self.myEqual(res[0]['label'], shows[1]['label'])

#        print(res)
#        res = [iteminfo(item) for item in get_items().values()]


if __name__ == '__main__':
    unittest.main()

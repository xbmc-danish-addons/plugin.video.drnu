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
menudata = (userdata/'menudata')
menudata.mkdir(parents=True, exist_ok=True)

handle = addon.DrDkTvAddon(plugin_url=plugin_url, plugin_handle=1)
handle._plugin_handle = {}

UPDATE_TESTS = True


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
        self.myEqual(len(episodes), 29)

        addon.addon.settings['disable.kids.seasons'] = 'false'
        handle.route(bluey['url'])
        episodes = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(episodes), 2)

    def test_a_aa(self):
        # A - AA
        handle._plugin_handle = {}
        main_menu = json.loads((menudata/'main_menu.json').read_text())
        handle.route(main_menu[1]['url'])
        a_aa = [iteminfo(item) for item in get_items().values()]
        self.assertTrue(len(a_aa) > 27)
        self.assertTrue(a_aa[0]['label'] == 'A')

        handle.route(a_aa[0]['url'])
        a = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(a), 102)

        self.myEqual(a[0]['label'], 'A Very British Scandal')
        handle.route(a[0]['url'])

    def test_search(self):
        handle._plugin_handle = {}
        handle.search()
        res = [iteminfo(item) for item in get_items().values()]
        self.myEqual(res[0]['label'], 'Series (13 found)')

        handle.route(res[0]['url'])
        res = [iteminfo(item) for item in get_items().values()]
        self.myEqual(len(res), 13)


if __name__ == '__main__':
    unittest.main()
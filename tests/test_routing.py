"""Integration tests for Routing functionality.

Golden JSON files under tests/userdata/menudata/ are compared against menu
output. Regenerate with: pytest --update-golden tests/test_routing.py
"""
import json
import urllib.parse as urlparse


from resources.lib import addon

plugin_url = 'plugin://plugin.video.drnu/'

# module-level flag kept for the --update-golden option (see conftest.py)
UPDATE_TESTS = False


def get_items(handle):
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


def assert_golden(menudata_dir, name, items, update):
    """Compare items against golden JSON; optionally rewrite the golden file."""
    golden = menudata_dir / name
    if update:
        golden.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    assert json.loads(golden.read_text()) == items


def main_menu_items(handle):
    handle.showMainMenu('drtv')
    return [iteminfo(item) for item in get_items(handle).values()]


def test_mainmenu(handle, menudata_dir):
    assert_golden(menudata_dir, 'main_menu.json', main_menu_items(handle), UPDATE_TESTS)


def test_daglige_forslag(handle, menudata_dir):
    main_menu = main_menu_items(handle)
    assert main_menu[2]['label'] == 'Daglige forslag'
    handle.route(main_menu[2]['url'])
    menu = [iteminfo(item) for item in get_items(handle).values()]
    assert_golden(menudata_dir, 'daglige_forslag.json', menu, UPDATE_TESTS)


def test_storste_programmer(handle, menudata_dir):
    main_menu = main_menu_items(handle)
    assert main_menu[3]['label'] == 'De største programmer lige nu'
    handle.route(main_menu[3]['url'])
    menu = [iteminfo(item) for item in get_items(handle).values()]
    assert_golden(menudata_dir, 'største_programmer.json', menu, UPDATE_TESTS)


def test_ramasjang(handle):
    handle.route('?area=ramasjang')
    a_aa = [iteminfo(item) for item in get_items(handle).values()]
    bluey = item_from_label(a_aa, 'Bluey')
    assert bluey, 'Bluey not found in ramasjang A-Å list'

    addon.addon.settings['disable.kids.seasons'] = 'true'
    handle.route(bluey['url'])
    episodes = [iteminfo(item) for item in get_items(handle).values()]
    assert len(episodes) == 12

    addon.addon.settings['disable.kids.seasons'] = 'false'
    handle.route(bluey['url'])
    episodes = [iteminfo(item) for item in get_items(handle).values()]
    assert len(episodes) == 12

    addon.addon.settings['disable.kids.menu'] = 'false'
    handle.route('?area=ramasjang')
    home_items = [iteminfo(item) for item in get_items(handle).values()]
    from_home = item_from_label(home_items, 'Skab med Ramasjang')
    assert from_home, 'Skab med Ramasjang not found in ramasjang home menu'
    handle.route(from_home['url'])
    episodes = [iteminfo(item) for item in get_items(handle).values()]
    assert len(episodes) == 5


def test_gensyn(handle):
    handle.route('?area=gensyn')
    items = [iteminfo(item) for item in get_items(handle).values()]

    # Årtier
    aartier = item_from_label(items, 'Årtier')
    assert aartier, 'Årtier not found in gensyn menu'
    handle.route(aartier['url'])
    items2 = [iteminfo(item) for item in get_items(handle).values()]

    # 1990'erne
    halvfems = item_from_label(items2, "1990'erne")
    assert halvfems, "1990'erne not found in Årtier menu"
    handle.route(halvfems['url'])
    episodes = [iteminfo(item) for item in get_items(handle).values()]
    assert item_from_label(episodes, 'Casper & Mandrilaftalen 1'), \
        'Casper & Mandrilaftalen 1 not found in 1990-episode list'


def test_a_aa(handle, menudata_dir):
    main_menu_js = json.loads((menudata_dir / 'main_menu.json').read_text())

    # A - AA
    handle.route(main_menu_js[1]['url'])
    a_aa = [iteminfo(item) for item in get_items(handle).values()]
    assert len(a_aa) > 27
    assert a_aa[0]['label'] == 'A'

    handle.route(a_aa[0]['url'])
    a = [iteminfo(item) for item in get_items(handle).values()]
    assert len(a) > 100
    assert a[0]['label'] == 'A Storm Foretold - det amerikanske oprør'


def test_search(handle):
    handle.search()
    res = [iteminfo(item) for item in get_items(handle).values()]
    assert res[0]['label'] == 'Series (14 found)'

    handle.route(res[0]['url'])
    res = [iteminfo(item) for item in get_items(handle).values()]
    assert len(res) == 14


def test_route_dispatch(handle):
    """route() dispatch table: query string -> expected item count and first label."""
    expected = {
        '?show=areaselector': (19, '30001'),  # dialog stub selects DR TV -> main menu
        '?area=drtv': (19, '30001'),
        '?area=gensyn': (19, 'De største gensyn lige nu'),
    }
    for query, (count, first_label) in expected.items():
        handle.route(query)
        items = [iteminfo(item) for item in get_items(handle).values()]
        assert len(items) == count, query
        assert items[0]['label'] == first_label, query

    # kids area with default settings (disable.kids.menu=true) unfolds the A-Å lists
    handle.route('?area=ramasjang')
    items = [iteminfo(item) for item in get_items(handle).values()]
    assert len(items) > 200
    assert item_from_label(items, 'Bluey'), 'Bluey missing from ramasjang A-Å'

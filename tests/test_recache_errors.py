"""Tests for request timeouts in drauth.py and continue-on-error in recache_items.

Both guard the background re-cache service: a stalled login used to block the
crawl indefinitely, and a single failing item used to abort the whole crawl.
"""
from resources.lib import drauth, tvapi
from resources.lib.constants import GET_TIMEOUT


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, content=b'', url='https://x/'):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.content = content
        self.text = ''
        self.url = url

    def json(self):
        return self._json


class FakeRequests:
    """Stands in for the requests module, returning queued responses in order."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _next(self, method, kwargs):
        self.calls.append({'method': method, 'timeout': kwargs.get('timeout')})
        return self.responses.pop(0)

    def get(self, *args, **kwargs):
        return self._next('get', kwargs)

    def post(self, *args, **kwargs):
        return self._next('post', kwargs)

    def Session(self):  # noqa: N802 - mirrors requests.Session
        return self

    def timeouts(self):
        return [c['timeout'] for c in self.calls]


def test_oidc_token_sends_timeout(monkeypatch):
    fake = FakeRequests([FakeResponse(json_data={'access_token': 'a'})])
    monkeypatch.setattr(drauth, 'requests', fake)
    assert drauth.oidc_token({}) == {'access_token': 'a'}
    assert fake.timeouts() == [GET_TIMEOUT]


def test_exchange_token_sends_timeout(monkeypatch):
    fake = FakeRequests([FakeResponse(json_data={'Token': 't'})])
    monkeypatch.setattr(drauth, 'requests', fake)
    assert drauth.exchange_token({'access_token': 'a', 'id_token': 'i'}) == {'Token': 't'}
    assert fake.timeouts() == [GET_TIMEOUT]


def test_anonymous_tokens_sends_timeout(monkeypatch):
    fake = FakeRequests([FakeResponse(content=b'[{"Token": "t"}]')])
    monkeypatch.setattr(drauth, 'requests', fake)
    assert drauth.anonymous_tokens() == [{'Token': 't'}]
    assert fake.timeouts() == [GET_TIMEOUT]


def test_full_login_sends_timeout_on_every_call(monkeypatch):
    responses = [
        FakeResponse(url='https://login.dr.dk/oidc/authorize/trans123'),
        FakeResponse(json_data={}),
        FakeResponse(json_data={}),
        FakeResponse(json_data={'data': {'authenticate': {'href': 'https://login.dr.dk/cb'}}}),
        FakeResponse(url='https://www.dr.dk/drtv/callback?code=abc'),
        FakeResponse(json_data={'access_token': 'a', 'id_token': 'i'}),
    ]
    fake = FakeRequests(responses)
    monkeypatch.setattr(drauth, 'requests', fake)
    assert drauth.full_login('user', 'pass') == {'access_token': 'a', 'id_token': 'i'}
    assert fake.timeouts() == [GET_TIMEOUT] * 6


class FakeProgress:
    def __init__(self, canceled=False):
        self.canceled = canceled
        self.updates = []

    def iscanceled(self):
        return self.canceled

    def update(self, percent, msg):
        self.updates.append((percent, msg))


def _make_api():
    api = tvapi.Api.__new__(tvapi.Api)
    api.cachePath = None
    api.tr = lambda id: f'tr{id}'
    api.log_lines = []
    api.log = api.log_lines.append
    api.fetch_full_plot = False
    return api


def test_recache_items_skips_failing_item_and_continues():
    api = _make_api()
    unfolded = []

    api.get_programcard = lambda path, data=None, use_cache=True: {
        'entries': [
            {'type': 'ListEntry', 'title': 'Broken', 'list': {'name': 'Broken'}},
            {'type': 'ListEntry', 'title': 'Fine', 'list': {'name': 'Fine'}},
        ]
    }

    def unfold_list(item, progress=None):
        unfolded.append(item['name'])
        if item['name'] == 'Broken':
            raise tvapi.ApiException('503 after retries')
        return []

    api.unfold_list = unfold_list
    children = []

    def get_children_front_items(channel, progress=None):
        children.append(channel)
        if channel == 'minisjang':
            raise tvapi.ApiException('timeout')
        return []

    api.get_children_front_items = get_children_front_items

    api.recache_items(progress=FakeProgress())

    # the broken item did not stop the crawl
    assert unfolded == ['Broken', 'Fine']
    assert children == ['ramasjang', 'minisjang', 'ultra']
    # both failures were logged
    assert len(api.log_lines) == 2
    assert 'Broken' in api.log_lines[0]
    assert 'minisjang' in api.log_lines[1]


def test_recache_items_still_aborts_on_progress_cancel():
    api = _make_api()
    api.get_programcard = lambda path, data=None, use_cache=True: {'entries': []}
    children = []
    api.get_children_front_items = lambda channel, progress=None: children.append(channel)

    api.recache_items(progress=FakeProgress(canceled=True))

    # aborted before the first channel, nothing logged as an error
    assert children == []
    assert api.log_lines == []


def test_recache_items_passes_progress_to_children_crawl():
    """The children's crawl must receive the progress object so it can abort
    when the user becomes active or the deadline passes."""
    api = _make_api()
    api.get_programcard = lambda path, data=None, use_cache=True: {'entries': []}
    seen = {}

    def get_children_front_items(channel, progress=None):
        seen[channel] = progress

    api.get_children_front_items = get_children_front_items
    progress = FakeProgress()

    api.recache_items(progress=progress)

    assert seen == {'ramasjang': progress, 'minisjang': progress, 'ultra': progress}


def test_get_children_front_items_threads_progress_into_unfold():
    api = _make_api()
    api.get_programcard = lambda path, data=None, use_cache=True: {
        'entries': [{'type': 'ListEntry', 'list': {'name': 'x'}}]}
    seen = {}

    def unfold_list(item, progress=None):
        seen['progress'] = progress
        return []

    api.unfold_list = unfold_list
    progress = FakeProgress()

    api.get_children_front_items('ramasjang', progress=progress)

    assert seen['progress'] is progress


def test_log_recache_error_tolerates_missing_logger():
    api = _make_api()
    api.log = None
    api._log_recache_error('something', RuntimeError('boom'))

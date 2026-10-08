"""Tests for the auth-response handling in drauth.full_login.

The authenticate mutation can return an Error (code/message) for a rejected
login instead of an href; assuming href raised a KeyError.
"""
from resources.lib import drauth


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, url='https://x/', text=''):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.url = url
        self.text = text

    def json(self):
        return self._json


class FakeRequests:
    """Returns queued responses in order and records call timeouts."""

    def __init__(self, responses):
        self.responses = list(responses)

    def _next(self, kwargs):
        return self.responses.pop(0)

    def get(self, *args, **kwargs):
        return self._next(kwargs)

    def post(self, *args, **kwargs):
        return self._next(kwargs)

    def Session(self):  # noqa: N802 - mirrors requests.Session
        return self


def _login_responses(authenticate):
    return [
        FakeResponse(url='https://login.dr.dk/oidc/authorize/trans123'),
        FakeResponse(json_data={}),
        FakeResponse(json_data={}),
        FakeResponse(json_data={'data': {'authenticate': authenticate}}),
    ]


def test_rejected_login_returns_error_not_keyerror(monkeypatch):
    authenticate = {'__typename': 'Error', 'code': 'AUTHENTICATION_FAILED',
                    'message': 'Wrong username or password'}
    fake = FakeRequests(_login_responses(authenticate))
    monkeypatch.setattr(drauth, 'requests', fake)

    result = drauth.full_login('user', 'wrong')

    assert 'error' in result
    assert result['error'] == 'Wrong username or password'


def test_missing_href_falls_back_to_code(monkeypatch):
    fake = FakeRequests(_login_responses({'__typename': 'Error', 'code': 'SOMETHING'}))
    monkeypatch.setattr(drauth, 'requests', fake)

    result = drauth.full_login('user', 'wrong')

    assert result['error'] == 'SOMETHING'


def test_successful_login_still_follows_href(monkeypatch):
    responses = _login_responses({'href': 'https://login.dr.dk/cb'}) + [
        FakeResponse(url='https://www.dr.dk/drtv/callback?code=abc'),
        FakeResponse(json_data={'access_token': 'a', 'id_token': 'i'}),
    ]
    fake = FakeRequests(responses)
    monkeypatch.setattr(drauth, 'requests', fake)

    assert drauth.full_login('user', 'pass') == {'access_token': 'a', 'id_token': 'i'}

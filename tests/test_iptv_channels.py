"""Tests for IPTV channel filtering in DrDkTvAddon.getIptvLiveChannels.

DR renamed the channel whose preset is 4 to 'TVA Live'; the include-setting
kept its original 'drtv' id. Building the setting name straight from the
title read 'iptv.channels.include.tvalive', which is undefined and therefore
false, so the channel never reached IPTV Manager even when DRTV was enabled.
"""
from resources.lib import addon as addon_module


def _channel(title, cid):
    return {'title': title,
            'item': {'id': str(cid), 'images': {'logo': f'logo{cid}.png'}}}


def test_tvalive_uses_the_drtv_include_setting(handle, monkeypatch):
    monkeypatch.setattr(handle.api, 'getLiveTV', lambda: [_channel('TVA Live', 1)])
    monkeypatch.setattr(handle.api, 'get_channel_url', lambda channel, subtitles=False: 'http://stream')
    monkeypatch.setattr(addon_module, 'bool_setting',
                        lambda name, default=False: name == 'iptv.channels.include.drtv')

    channels = handle.getIptvLiveChannels()

    assert [c['name'] for c in channels] == ['TVA Live']
    assert channels[0]['preset'] == addon_module.tvapi.CHANNEL_PRESET['TVA Live']
    assert channels[0]['id'] == 'drnu.1'


def test_tvalive_skipped_when_drtv_disabled(handle, monkeypatch):
    monkeypatch.setattr(handle.api, 'getLiveTV', lambda: [_channel('TVA Live', 1)])
    monkeypatch.setattr(addon_module, 'bool_setting', lambda name, default=False: False)

    assert handle.getIptvLiveChannels() == []

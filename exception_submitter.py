import os
import sys
import traceback as tb
import datetime
import urllib2
import simplejson
import random

import xbmcgui
import xbmcaddon

def handle_exception():
    # start by logging the usual info to syserr
    (type, value, traceback) = sys.exc_info()
    tb.print_exception(type, value, traceback)

    addon = xbmcaddon.Addon()
    heading = addon.getLocalizedString(random.randint(99980, 99985))
    line1 = addon.getLocalizedString(99990)
    line2 = addon.getLocalizedString(99991)
    line3 = addon.getLocalizedString(99992)
    yes = addon.getLocalizedString(99993)
    no = addon.getLocalizedString(99994)
    thanks = addon.getLocalizedString(99995)

    if xbmcgui.Dialog().yesno(heading, line1, line2, line3, no, yes):
        data = gather_data(addon, type, value, traceback)
        submit_data(data)

        xbmcgui.Dialog().ok(heading, thanks)

def gather_data(addon, type, value, traceback):
    (sysname, nodename, release, version, machine) = os.uname()

    data = dict()
    data['timestamp'] = datetime.datetime.now().isoformat()

    system = dict()
    system['nodename'] = nodename
    system['sysname'] = sysname
    system['release'] = release
    system['version'] = version
    system['machine'] = machine
    data['system'] = system

    addonInfo = dict()
    addonInfo['id'] = addon.getAddonInfo('id')
    addonInfo['name'] = addon.getAddonInfo('name')
    addonInfo['version'] = addon.getAddonInfo('version')
    addonInfo['path'] = addon.getAddonInfo('path')
    addonInfo['profile'] = addon.getAddonInfo('profile')
    data['addon'] = addonInfo

    execution = dict()
    execution['python'] = sys.version
    execution['sys.argv'] = sys.argv
    data['execution'] = execution

    exception = dict()
    exception['type'] = str(type)
    exception['value'] = str(value)
    exception['stacktrace'] = tb.format_tb(traceback)
    data['exception'] = exception

    return simplejson.dumps(data)

def submit_data(data):
    req = urllib2.Request('http://tommy.winther.nu/exception/submit.php', data)
    req.add_header('Content-Type', 'text/json')
    u = urllib2.urlopen(req)
    u.read()
    u.close()

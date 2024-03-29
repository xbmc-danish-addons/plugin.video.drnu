# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""This file implements the Kodi xbmcgui module, either using stubs or alternative functionality"""

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
from xbmcextra import kodi_to_ansi
from xbmc import VideoInfoTag


class Control:
    """A reimplementation of the xbmcgui Control class"""

    def __init__(self):
        """A stub constructor for the xbmcgui Control class"""

    @staticmethod
    def addControl(pControl):
        """A stub implementation for the xbmcgui Control class addControl() method"""

    @staticmethod
    def doModal():
        """A stub implementation for the xbmcgui Control class doModal() method"""

    @staticmethod
    def getId():
        """A stub implementation for the xbmcgui Control class getId() method"""
        return 0

    @staticmethod
    def selectItem(index):
        """A stub implementation for the xbmcgui Control class selectItem() method"""

    @staticmethod
    def setAnimations(eventAttr):
        """A stub implementation for the xbmcgui Control class setAnimations() method"""

    @staticmethod
    def setEnabled(enabled):
        """A stub implementation for the xbmcgui Control class setEnabled() method"""

    @staticmethod
    def setFocus(pControl):
        """A stub implementation for the xbmcgui Control class setFocus() method"""

    @staticmethod
    def setImage(imageFilename, useCache=True):
        """A stub implementation for the xbmcgui Control class setImage() method"""

    @staticmethod
    def setPosition(x, y):
        """A stub implementation for the xbmcgui Control class setPosition() method"""

    @staticmethod
    def setVisible(visible):
        """A stub implementation for the xbmcgui Control class setVisible() method"""


class ControlButton(Control):
    """A reimplementation of the xbmcgui ControlButton class"""

    def __init__(self, 
                x, y, width, height, label, focusTexture=None, 
                noFocusTexture=None, textOffsetX=10, textOffsetY=2, alignment=4, font=None,
                textColor=None, disabledColor=None, angle=0, shadowColor=None, focusedColor=None
                ):
        """A stub constructor for the xbmcgui Control class"""
        super(ControlButton, self).__init__()


class ControlImage(Control):
    """A reimplementation of the xbmcgui ControlImage class"""

    def __init__(self, x, y, width, height, filename, aspectRatio=0, colorDiffuse=None):
        """A stub constructor for the xbmcgui Control class"""
        super(ControlImage, self).__init__()


class ControlLabel(Control):
    """A reimplementation of the xbmcgui ControlLabel class"""

    def __init__(self,
                 x, y, width, height, label, font=None, textColor=None, 
                 disabledColor=None, alignment=0, hasPath=False, angle=0
                 ):
        """A stub constructor for the xbmcgui ControlLabel class"""

    @staticmethod
    def getLabel():
        """A stub implementation for the xbmcgui ControlLabel class getLabel() method"""
        return 'Label'

    @staticmethod
    def setLabel(label='', font=None, textColor=None, disabledColor=None, shadowColor=None, focusedColor=None, label2=''):
        """A stub implementation for the xbmcgui ControlLabel class getLabel() method"""


class ControlTextBox(Control):
    """A reimplementation of the xbmcgui ControlTextiBox class"""

    def __init__(self, x, y, width, height, font=None, textColor=None):  # pylint: disable=super-init-not-called
        """A stub constructor for the xbmcgui ControlLabel class"""

    @staticmethod
    def setText(text):
        """A stub implementation for the xbmcgui Control class setText() method"""
        print(kodi_to_ansi(text))


class Dialog:
    """A reimplementation of the xbmcgui Dialog class"""

    def __init__(self):
        """A stub constructor for the xbmcgui Dialog class"""

    @staticmethod
    def notification(heading, message, icon=None, time=None, sound=None):
        """A working implementation for the xbmcgui Dialog class notification() method"""
        heading = kodi_to_ansi(heading)
        message = kodi_to_ansi(message)
        print('\033[37;44;1mNOTIFICATION:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, message))

    @staticmethod
    def ok(heading, message='', line1='', line2='', line3=''):
        """A stub implementation for the xbmcgui Dialog class ok() method"""
        heading = kodi_to_ansi(heading)
        message = kodi_to_ansi(message)
        print('\033[37;44;1mOK:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, message or line1))

    @staticmethod
    def info(listitem):
        """A stub implementation for the xbmcgui Dialog class info() method"""

    @staticmethod
    def select(heading, opt_list, autoclose=0, preselect=None, useDetails=False):
        """A stub implementation for the xbmcgui Dialog class select() method"""
        if preselect is None:
            preselect = []
        heading = kodi_to_ansi(heading)
        print('\033[37;44;1mSELECT:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, ', '.join(opt_list)))
        return -1

    @staticmethod
    def multiselect(heading, options, autoclose=0, preselect=None, useDetails=False):  # pylint: disable=useless-return
        """A stub implementation for the xbmcgui Dialog class multiselect() method"""
        if preselect is None:
            preselect = []
        heading = kodi_to_ansi(heading)
        print('\033[37;44;1mMULTISELECT:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, ', '.join(options)))
        return None

    @staticmethod
    def contextmenu(items):
        """A stub implementation for the xbmcgui Dialog class contextmenu() method"""
        print('\033[37;44;1mCONTEXTMENU:\033[35;49;1m \033[37;1m%s\033[39;0m' % (', '.join(items)))
        return -1

    @staticmethod
    def yesno(heading, message='', line1='', line2='', line3='', nolabel=None, yeslabel=None, autoclose=0):
        """A stub implementation for the xbmcgui Dialog class yesno() method"""
        heading = kodi_to_ansi(heading)
        message = kodi_to_ansi(message)
        print('\033[37;44;1mYESNO:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, message or line1))
        return True

    @staticmethod
    def textviewer(heading, text=None, usemono=None):
        """A stub implementation for the xbmcgui Dialog class textviewer() method"""
        heading = kodi_to_ansi(heading)
        text = kodi_to_ansi(text)
        print('\033[37;44;1mTEXTVIEWER:\033[35;49;1m [%s]\n\033[37;1m%s\033[39;0m' % (heading, text))

    @staticmethod
    def browseSingle(type, heading, shares, mask=None, useThumbs=None, 
                     treatAsFolder=None, defaultt=None
                     ):
        """A stub implementation for the xbmcgui Dialog class browseSingle() method"""
        print('\033[37;44;1mBROWSESINGLE:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (type, heading))
        return 'special://masterprofile/addon_data/plugin.video.vrt.nu/'


class WindowDialog:
    """A reimplementation of the xbmcgui WindowDialog class"""

    def __init__(self):
        """A stub constructor for the xbmcgui Dialog class"""

    @staticmethod
    def notification(heading, message, icon=None, time=None, sound=None):
        """A working implementation for the xbmcgui Dialog class notification() method"""
        heading = kodi_to_ansi(heading)
        message = kodi_to_ansi(message)
        print('\033[37;44;1mNOTIFICATION:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, message))

    @staticmethod
    def ok(heading, message='', line1='', line2='', line3=''):
        """A stub implementation for the xbmcgui Dialog class ok() method"""
        heading = kodi_to_ansi(heading)
        message = kodi_to_ansi(message)
        print('\033[37;44;1mOK:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, message or line1))

    @staticmethod
    def info(listitem):
        """A stub implementation for the xbmcgui Dialog class info() method"""

    @staticmethod
    def select(heading, opt_list, autoclose=0, preselect=None, useDetails=False):
        """A stub implementation for the xbmcgui Dialog class select() method"""
        if preselect is None:
            preselect = []
        heading = kodi_to_ansi(heading)
        print('\033[37;44;1mSELECT:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, ', '.join(opt_list)))
        return -1

    @staticmethod
    def multiselect(heading, options, autoclose=0, preselect=None, useDetails=False):  # pylint: disable=useless-return
        """A stub implementation for the xbmcgui Dialog class multiselect() method"""
        if preselect is None:
            preselect = []
        heading = kodi_to_ansi(heading)
        print('\033[37;44;1mMULTISELECT:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, ', '.join(options)))
        return None

    @staticmethod
    def contextmenu(items):
        """A stub implementation for the xbmcgui Dialog class contextmenu() method"""
        print('\033[37;44;1mCONTEXTMENU:\033[35;49;1m \033[37;1m%s\033[39;0m' % (', '.join(items)))
        return -1

    @staticmethod
    def yesno(heading, message='', line1='', line2='', line3='', nolabel=None, yeslabel=None, autoclose=0):
        """A stub implementation for the xbmcgui Dialog class yesno() method"""
        heading = kodi_to_ansi(heading)
        message = kodi_to_ansi(message)
        print('\033[37;44;1mYESNO:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, message or line1))
        return True

    @staticmethod
    def textviewer(heading, text=None, usemono=None):
        """A stub implementation for the xbmcgui Dialog class textviewer() method"""
        heading = kodi_to_ansi(heading)
        text = kodi_to_ansi(text)
        print('\033[37;44;1mTEXTVIEWER:\033[35;49;1m [%s]\n\033[37;1m%s\033[39;0m' % (heading, text))

    @staticmethod
    def browseSingle(type, heading, shares, mask=None, useThumbs=None, 
                     treatAsFolder=None, defaultt=None
                     ):
        """A stub implementation for the xbmcgui Dialog class browseSingle() method"""
        print('\033[37;44;1mBROWSESINGLE:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (type, heading))
        return 'special://masterprofile/addon_data/plugin.video.vrt.nu/'


class DialogProgress:
    """A reimplementation of the xbmcgui DialogProgress"""

    def __init__(self):
        """A stub constructor for the xbmcgui DialogProgress class"""
        self.percent = 0

    def close(self):
        """A stub implementation for the xbmcgui DialogProgress class close() method"""
        self.percent = 0
        print()
        sys.stdout.flush()

    def create(self, heading, message='', line1='', line2='', line3=''):
        """A stub implementation for the xbmcgui DialogProgress class create() method"""
        self.percent = 0
        heading = kodi_to_ansi(heading)
        line1 = kodi_to_ansi(line1)
        print('\033[37;44;1mPROGRESS:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, message or line1))
        sys.stdout.flush()

    def iscanceled(self):
        """A stub implementation for the xbmcgui DialogProgress class iscanceled() method"""
        return self.percent > 5  # Cancel at 5%

    def update(self, percent, message='', line1='', line2='', line3=''):
        """A stub implementation for the xbmcgui DialogProgress class update() method"""
        if (percent - 5) < self.percent:
            return
        self.percent = percent
        line1 = kodi_to_ansi(line1)
        line2 = kodi_to_ansi(line2)
        line3 = kodi_to_ansi(line3)
        base_str = f'\033[1G\033[37;44;1mPROGRESS:\033[35;49;1m [{percent:d}%]'
        if line1 or line2 or line3:
            print(base_str + f'\033[37;1m{message or line1 or line2 or line3}\033[39;0m', end='')
        else:
            print(base_str + '\033[39;0m', end='')
        sys.stdout.flush()


class DialogProgressBG:
    """A reimplementation of the xbmcgui DialogProgressBG"""

    def __init__(self):
        """A stub constructor for the xbmcgui DialogProgressBG class"""
        self.percentage = 0

    @staticmethod
    def close():
        """A stub implementation for the xbmcgui DialogProgressBG class close() method"""
        print()

    @staticmethod
    def create(heading, message):
        """A stub implementation for the xbmcgui DialogProgressBG class create() method"""
        heading = kodi_to_ansi(heading)
        message = kodi_to_ansi(message)
        print('\033[37;44;1mPROGRESS:\033[35;49;1m [%s] \033[37;1m%s\033[39;0m' % (heading, message))

    @staticmethod
    def isfinished():
        """A stub implementation for the xbmcgui DialogProgressBG class isfinished() method"""

    def update(self, percentage, heading=None, message=None):
        """A stub implementation for the xbmcgui DialogProgressBG class update() method"""
        if (percentage - 5) < self.percentage:
            return
        self.percentage = percentage
        message = kodi_to_ansi(message)
        if message:
            print('\033[37;44;1mPROGRESS:\033[35;49;1m [%d%%] \033[37;1m%s\033[39;0m' % (percentage, message))
        else:
            print('\033[1G\033[37;44;1mPROGRESS:\033[35;49;1m [%d%%]\033[39;0m' % (percentage), end='')


class ListItem:
    """A reimplementation of the xbmcgui ListItem class"""

    def __init__(self, label='', label2='', path='', offscreen=False):
        """A stub constructor for the xbmcgui ListItem class"""
        self.label = kodi_to_ansi(label)
        self.label2 = kodi_to_ansi(label2)
        self.path = path
        self.offscreen = offscreen

        self.art = {}
        self.content_lookup = None
        self.context_menu = []
        self.info = {}
        self.info_type = None
        self.is_folder = False
        self.mimetype = None
        self.properties = {}
        self.rating = None
        self.stream_info = {}
        self.stream_type = None
        self.subtitles = []
        self.unique_ids = []
        self.infotag = VideoInfoTag()

    def addContextMenuItems(self, items, replaceItems=False):
        """A stub implementation for the xbmcgui ListItem class addContextMenuItems() method"""
        if replaceItems:
            self.context_menu = items
        else:
            self.context_menu += items

    def addStreamInfo(self, stream_type, stream_values):
        """A stub implementation for the xbmcgui LitItem class addStreamInfo() method"""
        self.stream_type = stream_type
        self.stream_info = stream_values

    def setArt(self, key):
        """A stub implementation for the xbmcgui ListItem class setArt() method"""
        self.art = key

    def setContentLookup(self, enable):
        """A stub implementation for the xbmcgui ListItem class setContentLookup() method"""
        self.content_lookup = enable

    def setInfo(self, type, infoLabels):  # pylint: disable=redefined-builtin
        """A stub implementation for the xbmcgui ListItem class setInfo() method"""
        self.info_type = type
        self.info = infoLabels

    def setIsFolder(self, isFolder):
        """A stub implementation for the xbmcgui ListItem class setIsFolder() method"""
        self.is_folder = isFolder

    def setMimeType(self, mimetype):
        """A stub implementation for the xbmcgui ListItem class setMimeType() method"""
        self.mimetype = mimetype

    def setPath(self, path):
        """A stub implementation for the xbmcgui ListItem class setPath() method"""
        self.path = path

    def setProperty(self, key, value):
        """A stub implementation for the xbmcgui ListItem class setProperty() method"""
        self.properties[key] = value

    def setProperties(self, dictionary):
        """A stub implementation for the xbmcgui ListItem class setProperties() method"""
        self.properties.update(dictionary)

    def setSubtitles(self, subtitleFiles):
        """A stub implementation for the xbmcgui ListItem class setSubtitles() method"""
        self.subtitles = subtitleFiles

    def setUniqueIDs(self, values, defaultrating=None):
        """A stub implementation for the xbmcgui ListItem class setUniqueIDs() method"""
        self.unique_ids = values
        self.rating = defaultrating

    def getVideoInfoTag(self):
        return self.infotag


class Window:
    """A reimplementation of the xbmcgui Window"""

    def __init__(self, existingwindowId=-1):
        """A stub constructor for the xbmcgui Window class"""
        return None

    @staticmethod
    def addControl(pControl):
        """A stub implementation for the xbmcgui Window class addControl() method"""

    def close(self):
        """A stub implementation for the xbmcgui Window class close() method"""

    def doModal(self):
        """A stub implementation for the xbmcgui Window class doModal() method"""
        self.onInit()
        self.onClick(self.button_run_id)

    @staticmethod
    def getControl(iControlId):
        """A stub implementation for the xbmcgui Window class getControl() method"""
        return Control()

    @staticmethod
    def getFocusId():
        """A stub implementation for the xbmcgui Window class getFocusId() method"""
        return 0

    @staticmethod
    def getProperty(key):
        """A stub implementation for the xbmcgui Window class getProperty() method"""
        return ''

    @staticmethod
    def setProperty(key, value):
        """A stub implementation for the xbmcgui Window class setProperty() method"""
        return

    @staticmethod
    def clearProperty(key):
        """A stub implementation for the xbmcgui Window class clearProperty() method"""
        return

    @staticmethod
    def setFocus(pControl):
        """A stub implementation for the xbmcgui Window class setFocus() method"""

    def show(self):
        """A stub implementation for the xbmcgui Window class show() method"""

    @staticmethod
    def onClick():
        """A stub implementation for the xbmcgui Window class onClick() method"""

    @staticmethod
    def onInit():
        """A stub implementation for the xbmcgui Window class onInit() method"""

    @staticmethod
    def button_run_id():
        """A stub implementation for the xbmcgui Window class button_run_id() method"""


class WindowXML(Window):
    """A reimplementation of the xbmcgui WindowXML"""

    def __init__(self, xmlFilename, scriptPath, defaultSkin='Default', defaultRes='720p'):
        """A stub constructor for the xbmcgui WindowXML class"""
        super(WindowXML, self).__init__()


class WindowXMLDialog(WindowXML):
    """A reimplementation of the xbmcgui WindowXMLDialog"""

    def __init__(self, xmlFilename, scriptPath, defaultSkin='Default', defaultRes='720p'):
        """A stub constructor for the xbmcgui WindowXMLDialog class"""
        WindowXML.__init__(self, xmlFilename, scriptPath, defaultSkin, defaultRes)


def getCurrentWindowId():
    """A stub implementation of the xbmcgui getCurrentWindowId() method"""
    return 0

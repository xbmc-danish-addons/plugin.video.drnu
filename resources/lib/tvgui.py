#
#      Copyright (C) 2014 Tommy Winther, msj33, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os

import xbmcaddon
import xbmcgui
import xbmc

class AreaSelectorDialog(xbmcgui.WindowDialog):
    def __init__(self):
        self.areaSelected = 'none'

        ADDON = xbmcaddon.Addon()

        # Background
        background = xbmcgui.ControlImage(0, 0, 1280, 720, os.path.join(ADDON.getAddonInfo('path'), 'resources', 'fanart.jpg'))

        title = xbmcgui.ControlLabel(0, 60, 1280, 60, "[B]%s[/B][CR]%s" % (ADDON.getLocalizedString(30100), ADDON.getLocalizedString(30101)), 'font30', alignment=2)

        self.drTvButton = xbmcgui.ControlButton(70, 210, 300, 300, "drtv",
                                                focusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-drtv-focus.png'),
                                                noFocusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-drtv.png')
                                                )

        self.ramasjangButton = xbmcgui.ControlButton(490, 210, 300, 300, "ramasjang",
                                                     focusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-ramasjang-focus.png'),
                                                     noFocusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-ramasjang.png')
                                                     )

        self.ultraButton = xbmcgui.ControlButton(910, 210, 300, 300, "ultra",
                                                 focusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-ultra-focus.png'),
                                                 noFocusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-ultra.png')
                                                 )
#        self.ultraButton.mylabel = 'ultra'

        self.addControls([background, title, self.drTvButton, self.ramasjangButton, self.ultraButton])

        self.drTvButton.controlRight(self.ramasjangButton)
        self.drTvButton.controlLeft(self.ultraButton)
        self.ramasjangButton.controlLeft(self.drTvButton)
        self.ramasjangButton.controlRight(self.ultraButton)
        self.ultraButton.controlLeft(self.ramasjangButton)
        self.ultraButton.controlRight(self.drTvButton)

        self.setFocus(self.drTvButton)

#    def onAction(self, control):
#        xbmc.log('action ' + str(control.getLabel())+ '+ '+ str(control.getLabel2()), xbmc.LOGINFO )


    def onControl(self, control):
        xbmc.log('gui ' + str(control.getLabel() ), xbmc.LOGINFO )
        self.areaSelected = control.getLabel()

        # if control == self.drTvButton:
        #     self.areaSelected = 'drtv'
        # elif control == self.ramasjangButton:
        #     self.areaSelected = 'ramasjang'
        # elif control == self.ultraButton:
        #     self.areaSelected = 'ultra'

        self.close()
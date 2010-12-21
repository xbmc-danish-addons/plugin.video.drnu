import os
import re
import sys
import unittest

sys.path.append("../script.module.danishaddons/")
sys.path.append("../script.module.danishaddons/xbmcstubs/")
sys.path.append("../script.module.feedparser/")

import xbmcplugin
import xbmcaddon
import danishaddons
import drnu as addon

class TestDRNUPlayer(unittest.TestCase):

    def setUp(self):
        danishaddons.init([os.getcwd(), '12345', ''])
        xbmcplugin.items = list()

    def testGetProgramSeries(self):
        xbmcaddon.strings[30004] = 'plotoutline: %s'
        addon.getProgramSeries()

        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')

if __name__ == '__main__':
    unittest.main()
    
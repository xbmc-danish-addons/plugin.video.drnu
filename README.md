# plugin.video.drnu
![Kodi Version](https://img.shields.io/badge/kodi%20version-19.x-blue)
[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fxbmc-danish-addons%2Fplugin.video.drnu%2Fbadge%3Fref%3Dmaster&style=flat)](https://actions-badge.atrox.dev/xbmc-danish-addons/plugin.video.drnu/goto?ref=master)
[![License](https://img.shields.io/github/license/xbmc-danish-addons/plugin.video.drnu)](https://github.com/xbmc-danish-addons/plugin.video.drnu/blob/master/LICENSE.txt)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)


## Known issues
before version 5.1.1
 - *inputstream.ffmpegdirect* fail to skip in streams and resume playback in the middle of a stream.

Version 5.1.1

*Inputstream.adaptive* has two known issues that are now resolved. You can find your current installed version of inputstream.adaptive in the inputstream.helper addon.
- version 19.0.4 and earlier will make kodi crash on most streams from dr.dk today.
- version 19.0.5 will stop playback after 10seconds on some streams, and fail to skip in stream within the first 10minutes of the stream.

version 19.0.6 have no known issues. On Android and Windows it should update automatically to latest. On linux it is compiled together with kodi, and is provided together with the kodi package. Please push your package provider of kodi to update inputstream.adaptive to latest.


Version 5.1.2 (only here at github releases)

Has an exftra setting to switch between *adaptive* and *ffmpegdirect*

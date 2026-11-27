#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
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
"""Constants for the DR API endpoints, channels and content areas."""

# Channel ids are UUIDs on the drtv-platform API; the numeric ids in the
# paths ("/kanal/dr1_20875") are only the legacy slug suffix.
CHANNEL_IDS = [
    '4b2f55f1-0a85-469a-b751-81617f455938',  # DR1
    '1d3b66b5-c688-4127-99d7-ab648bff6c85',  # DR2
    'ca6083dc-5c28-442a-b539-f5c0b3564a98',  # TVA Live
    '6bb0aa9b-4063-4bfd-88e8-643d3eba3617',  # DR Ramasjang
]
# DRTV Ekstra (the old fifth channel) is not on the new API any more.
CHANNEL_PRESET = {
    'DR1': 1,
    'DR2': 2,
    'DR Ramasjang': 3,
    'TVA Live': 4,
}
URL = 'https://api.drtv-platform.dr.dk/api'
CLIENT_ID = '283ba39a2cf31d3b81e922b8'
GET_TIMEOUT = 10
A_AA = {
    'ramasjang': '/ramasjang_a-aa',
    'minisjang': '/minisjang/a-aa',
    'ultra': '/ultra_a-aa',
    'drtv': '/kategorier/a-aa',
    'gensyn': '/gensyn/a-aa',
}

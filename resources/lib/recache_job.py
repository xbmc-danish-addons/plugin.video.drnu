from tvapi import Api
from pathlib import Path
import sys


def tr(id, da=True):
    msgid = str(id)
    msgstr = str(id)

    if id == 30506:
        msgid = "Hard-of-hearing"
        msgstr = "For hørehæmmede"

    if id == 30507:
        msgid = "Subtitles"
        msgstr = "Undertekster"

    if id == 30508:
        msgid = "empty"
        msgstr = "Ingen undertekster"

    if da:
        return msgstr
    else:
        return msgid


if len(sys.argv) != 2:
    print('please give cache folder as argument')
    sys.exit(0)

cachepath = Path(sys.argv[1])
api = Api(cachepath, tr)
api.recache_requests(cache_urls=False, cache_episodes=True, clear_expired=False, verbose=True)

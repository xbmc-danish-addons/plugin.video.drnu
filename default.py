# -*- coding: utf-8 -*-
import asyncio
from resources.lib import addon
import sys
sys.modules['_asyncio'] = None

# Start of Module
if __name__ == "__main__":
    handle = addon.DrDkTvAddon(plugin_url=sys.argv[0], plugin_handle=int(sys.argv[1]))
    asyncio.run(handle.route(sys.argv[2]))

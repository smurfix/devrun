# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This file is part of devrun, a comprehensive controller and monitor for
## various typed code.
##
## devrun is Copyright © 2016 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.rst` for details,
## including optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP

import asyncio
import sys

from . import BaseDevice

class Device(BaseDevice):
    """Test device for syncing"""
    help = """\
This is the Ping device.
It prints 'Ping from ‹name›' every second, or however often you set it to.
"""

    q = None
    async def run(self):
        cfg = self.loc.get('config',{})
        w = cfg.get('want',None)
        await asyncio.sleep(cfg.get('delay',5))
        if w is not None:
            dev = await self.cmd.reg.test.get(w)
            n = 1
            self.cmd.reg.test[self.name] = self
            while True:
                await dev.q.put((self.name,n))
                print("Pling sent ",n)
                await asyncio.sleep(cfg.get('interval',1), loop=self.cmd.loop)
                n += 1
        else:
            self.q = asyncio.Queue(cfg.get('qlen',5))
            self.cmd.reg.test[self.name] = self
            while True:
                r = await self.q.get()
                print("Pling got ",r)
                await asyncio.sleep(cfg.get('interval',1), loop=self.cmd.loop)

    @property
    def state(self):
        res = super().state
        if self.q is not None:
            res['q_len'] = self.q.qsize()
        return res

Device.register("config","interval", cls=float, doc="Interval between pings")
Device.register("config","delay", cls=float, doc="Initial delay")
Device.register("config","qlen", cls=int, doc="Queue length")
Device.register("config","want", cls=str, doc="destination")


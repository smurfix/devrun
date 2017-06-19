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
This is the Pling device.
It creates a master/slave system for testing.
Pling devices with a "want" config parameter send messages to another pling
device with no "want" parameter, which will queue and print them.

Configuring a slave to send to anoher slave will result in an error.
"""

    q = None
    async def run(self):
        cfg = self.cfg
        w = cfg.get('want',None)
        await asyncio.sleep(cfg.get('delay',5))
        if w is not None:
            dev = await self.cmd.reg.test.get(w)
            self.cmd.reg.test[self.name] = self
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

    def get_state(self):
        res = super().get_state()
        if self.q is not None:
            res['q_len'] = self.q.qsize()
        return res

Device.register("config","interval", cls=float, doc="Interval between pings")
Device.register("config","delay", cls=float, doc="Initial delay")
Device.register("config","qlen", cls=int, doc="Queue length")
Device.register("config","want", cls=str, doc="destination")


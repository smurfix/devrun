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
import blinker

from . import BaseDevice
from devrun.support.abl import RT,Request,Reply

class Device(BaseDevice):
    """SDM630 power meters"""
    help = """\
This module interfaces to an SDM630 power meter via Modbus.
"""

    async def query(self,func,b=None):
        return (await self.bus.query(self.adr,func,b))

    async def floats(self, start,len):
        rr = self.bus.read_input_registers(start*2-2,len*2, unit=self.adr)

    async def run(self):
        self.signal = blinker.signal(self.name)
        self.trigger = asyncio.Event()

        self.amp = [0]*4
        self.watt = [0]*4
        self.VA = [0]*4
        self.factor = [0]*4
        self.in_use = False

        cfg = self.loc.get('config',{})
        ### auto mode
        self.bus = await self.cmd.reg.bus.get(cfg['bus'])
        self.adr = cfg['address']
        self.power = await self.cmd.reg.power.get(cfg['power'])

        val = await self.floats(172,1) # total
        self.last_total = abs(val[0])
        self.cmd.reg.meter[self.name] = self

        while True:
            # the abs() calls are here because sometimes
            # people connect their meters the wrong way
            val = await self.floats(4,12) # current,power,VA

            self.amps[1] = abs(val[0])
            self.amps[2] = abs(val[1])
            self.amps[3] = abs(val[2])

            self.watt[1] = abs(val[3])
            self.watt[2] = abs(val[4])
            self.watt[3] = abs(val[5])

            self.VA[1] = abs(val[6])
            self.VA[2] = abs(val[7])
            self.VA[3] = abs(val[8])

            self.factor[1] = abs(val[9])
            self.factor[2] = abs(val[10])
            self.factor[3] = abs(val[11])

            val = await self.floats(25,5) # totals
            self.amps[0] = abs(val[0])
            self.watt[0] = abs(val[2]) # 27
            self.VA[0] = abs(val[4]) # 29

            val = await self.floats(172,1) # total
            self.cur_total = abs(val[0]) - self.last_total
            self.signal.send(self)

            try:
                await asyncio.wait_for(self.trigger.wait(), cfg.get('interval' if self.in_use else 'idle',1))
            except asyncio.TimeoutError:
                pass
            else:
                self.trigger.clear()

    def used(self):
        self.in_use = True
        self.trigger.set()
        
    def unused(self):
        self.in_use = False
        
Device.register("config","bus", cls=str, doc="Bus to connect to")
Device.register("config","address", cls=int, doc="This charger's address on the bus")
Device.register("config","power", cls=str, doc="Power supply to use")
Device.register("config","interval", cls=float, doc="delay between measurements")
Device.register("config","idle", cls=float, doc="delay between measurements when (not in use)")


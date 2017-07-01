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
import blinker
import struct

from . import BusDevice
from devrun.support.modbus import ModbusException
from math import isnan

import logging
logger = logging.getLogger(__name__)

class Device(BusDevice):
    """Siemens Sentron PAC3200 power meters"""
    help = """\
This module interfaces to a Siemens Sentron PAC3200 power meter via Modbus.
"""

    async def prepare2(self):
        val = await self.doubles(801,2) # total
        self.last_total = abs(val[0])+abs(val[1])
        await super().prepare2()

    async def step1(self):
        await super().step1()
        while True:
            try:
                val = await self.floats(1,21) # current,power,VA

                self.volt[0] = abs(val[0+self.phase1])
                self.volt[1] = abs(val[0+self.phase2])
                self.volt[2] = abs(val[0+self.phase3])
                self.volts = sum(self.volt)/3

                self.amp[0] = abs(val[6+self.phase1])
                self.amp[1] = abs(val[6+self.phase2])
                self.amp[2] = abs(val[6+self.phase3])
                self.amp_max = max(self.amp)

                self.watt[0] = abs(val[12+self.phase1])
                self.watt[1] = abs(val[12+self.phase2])
                self.watt[2] = abs(val[12+self.phase3])

                self.VA[0] = abs(val[9+self.phase1])
                self.VA[1] = abs(val[9+self.phase2])
                self.VA[2] = abs(val[9+self.phase3])

                self.factor[0] = 1 if isnan(val[18+self.phase1]) else abs(val[18+self.phase1])
                self.factor[1] = 1 if isnan(val[18+self.phase2]) else abs(val[18+self.phase2])
                self.factor[2] = 1 if isnan(val[18+self.phase3]) else abs(val[18+self.phase3])

                val = await self.floats(63,2) # total
                self.VAs = abs(val[0])
                self.watts = abs(val[1])

                asum = sum(self.amp)
                if asum == 0:
                    self.factor_avg = 1
                else:
                    self.factor_avg = sum(self.amp[n]*self.factor[n] for n in (0,1,2))/asum

                val = await self.doubles(801,2) # total
                self.Whs = abs(val[0])+abs(val[1])
                self.cur_total = self.Whs - self.last_total
            except ModbusException as exc:
                logger.warning("%s: %s from %s:%s",self.name,exc, self.bus.name,self.unit)
            else:
                return

Device.register("config","bus", cls=str, doc="Bus to connect to")
Device.register("config","address", cls=int, doc="This charger's address on the bus")
Device.register("config","power", cls=str, doc="Power supply to use")
Device.register("config","offset", cls=int, doc="phase offset (0,1,2)")


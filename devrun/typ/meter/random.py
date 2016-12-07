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
from random import Random
from time import time

from . import BaseDevice
from devrun.support.abl import RT,Request,Reply
from devrun.support.modbus import ModbusException

import logging
logger = logging.getLogger(__name__)

class Device(BaseDevice):
    """A power meter used for testing which reports random power levels"""
    help = """\
This module implements a virtual meter that reports semi-random values.

The typical current level is 90% of the allowed range.
"""

    async def query(self,func,b=None):
        return (await self.bus.query(self.adr,func,b))

    async def floats(self, start,count):
        rr = await self.bus.read_input_registers(start*2-2,count*2, unit=self.adr)
        n = len(rr.registers)
        return struct.unpack('>%df'%(n//2),struct.pack('>%dH'%n,*rr.registers))

    def trigger(self):
        self._trigger.set()

    def register_charger(self,obj):
        assert self.charger is None
        self.charger = obj
        self._trigger.set()

    @property
    def in_use(self):
        if self.charger is None:
            return False
        else:
            return self.charger.charging

    def get_state(self):
        res = super().get_state()
        res['amps'] = self.amp
        res['amp'] = self.amp_max
        res['watts'] = self.watt
        res['watt'] = self.watts
        res['VAs'] = self.VA
        res['VA'] = self.VAs
        res['power_factors'] = self.factor
        res['power_factor'] = self.factor_avg
        res['energy_total'] = self.cur_total
        return res

    @property
    def rnd(self):
        if self.charger is None:
            return 0
        return self.rand.betavariate(10,1)*self.charger.A

    async def run(self):
        self.signal = blinker.Signal()
        self._trigger = asyncio.Event(loop=self.cmd.loop)
        self.charger = None
        self.cur_total = 0
        self.rand = Random()

        self.amp = [0]*3
        self.watt = [0]*3
        self.VA = [0]*3
        self.factor = [0]*3

        cfg = self.loc.get('config',{})
        self.min = cfg.get('min',0)
        self.max = cfg.get('max',32)
        self.power = await self.cmd.reg.power.get(cfg['power'])

        self.cmd.reg.meter[self.name] = self

        t1=0
        while True:
            # the abs() calls are here because sometimes
            # people connect their meters the wrong way
            self.amp[0] = self.rnd
            self.amp[1] = self.rnd
            self.amp[2] = self.rnd
            self.amp_max = max(self.amp)

            self.factor[0] = self.rand.betavariate(5,1)
            self.factor[1] = self.rand.betavariate(5,1)
            self.factor[2] = self.rand.betavariate(5,1)

            self.VA[0] = self.amp[0]*230
            self.VA[1] = self.amp[1]*230
            self.VA[2] = self.amp[2]*230

            self.watt[0] = self.VA[0]*self.factor[0]
            self.watt[1] = self.VA[1]*self.factor[1]
            self.watt[2] = self.VA[2]*self.factor[2]

            asum = sum(self.amp)
            if asum == 0:
                self.factor_avg = 1
            else:
                self.factor_avg = sum(self.amp[n]*self.factor[n] for n in (0,1,2))/asum

            self.amps = sum(self.amp)
            self.watts = sum(self.watt)
            self.VAs = sum(self.VA)

            self.cur_total += sum(self.watt[i]*t1/3600 for i in (0,1,2))
            logger.info("%s: amp %.1f %s pf %.3f watt %.1f va %.1f sum %.1f",self.name,
                self.amps, ','.join('%.2f' % x for x in self.amp),
                self.factor_avg,self.watts,self.VAs,self.cur_total)
            self.signal.send(self)

            t1 = time()
            try:
                delay = cfg.get('interval',1) if self.in_use else cfg.get('idle',30)
                await asyncio.wait_for(self._trigger.wait(), delay)
            except asyncio.TimeoutError:
                pass
            else:
                self._trigger.clear()
            t1 = time()-t1

Device.register("config","power", cls=str, doc="Power supply to use")
Device.register("config","interval", cls=float, doc="delay between measurements")
Device.register("config","idle", cls=float, doc="delay between measurements when the charger is not in use")
Device.register("config","min", cls=float, doc="minimum power usage")
Device.register("config","max", cls=float, doc="maximum power usage")


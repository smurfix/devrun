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

from . import BaseDevice
from devrun.support.modbus import ModbusException

import logging
logger = logging.getLogger(__name__)

class Device(BaseDevice):
    """SDM630 power meters"""
    help = """\
This module interfaces to an SDM630 power meter via Modbus.
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

    async def run(self):
        self.signal = blinker.Signal()
        self._trigger = asyncio.Event(loop=self.cmd.loop)
        self.charger = None
        self.cur_total = 0

        self.amp = [0]*3
        self.watt = [0]*3
        self.VA = [0]*3
        self.factor = [0]*3

        cfg = self.loc.get('config',{})
        ### auto mode
        self.bus = await self.cmd.reg.bus.get(cfg['bus'])
        self.adr = cfg['address']
        self.power = await self.cmd.reg.power.get(cfg['power'])
        self.phase1 = cfg.get('phase_offset',0)
        self.phase2 = (self.phase1+1)%3
        self.phase3 = (self.phase2+1)%3

        val = await self.floats(172,1) # total
        self.last_total = abs(val[0])*1000
        self.cmd.reg.meter[self.name] = self

        while True:
            # the abs() calls are here because sometimes
            # people connect their meters the wrong way
            try:
                val = await self.floats(4,15) # current,power,VA

                self.amp[0] = abs(val[self.phase1])
                self.amp[1] = abs(val[self.phase2])
                self.amp[2] = abs(val[self.phase3])
                self.amp_max = max(self.amp)

                self.watt[0] = abs(val[3+self.phase1])
                self.watt[1] = abs(val[3+self.phase2])
                self.watt[2] = abs(val[3+self.phase3])

                self.VA[0] = abs(val[6+self.phase1])
                self.VA[1] = abs(val[6+self.phase2])
                self.VA[2] = abs(val[6+self.phase3])

                self.factor[0] = abs(val[12+self.phase1])
                self.factor[1] = abs(val[12+self.phase2])
                self.factor[2] = abs(val[12+self.phase3])
                asum = sum(self.amp)
                if asum == 0:
                    self.factor_avg = 1
                else:
                    self.factor_avg = sum(self.amp[n]*self.factor[n] for n in (0,1,2))/asum

                val = await self.floats(25,5) # totals
                self.amps = abs(val[0])
                self.watts = abs(val[2]) # 27
                self.VAs = abs(val[4]) # 29

                val = await self.floats(172,1) # total
                self.cur_total = abs(val[0])*1000 - self.last_total
                logger.info("%s: amp %.1f %s pf %.3f watt %.1f va %.1f sum %.1f",self.name,
                    self.amps, ','.join('%.2f' % x for x in self.amp),
                    self.factor_avg,self.watts,self.VAs,self.cur_total)
                self.signal.send(self)
            except ModbusException as exc:
                logger.warning("%s: %s from %s:%s",self.name,exc, self.bus.name,self.adr)
                self._trigger.set()

            try:
                delay = cfg.get('interval',1) if self.in_use else cfg.get('idle',30)
                await asyncio.wait_for(self._trigger.wait(), delay)
            except asyncio.TimeoutError:
                pass
            else:
                self._trigger.clear()

Device.register("config","bus", cls=str, doc="Bus to connect to")
Device.register("config","address", cls=int, doc="This charger's address on the bus")
Device.register("config","power", cls=str, doc="Power supply to use")
Device.register("config","interval", cls=float, doc="delay between measurements")
Device.register("config","idle", cls=float, doc="delay between measurements when (not in use)")
Device.register("config","offset", cls=int, doc="phase offset (0,1,2)")


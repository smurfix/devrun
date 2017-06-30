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

"""\
This module implements talking to a power meter.

"""

import asyncio
import blinker
import struct
from time import time

from devrun.typ import BaseType
from devrun.device import BaseDevice as _BaseDevice

import logging
logger = logging.getLogger(__name__)

from devrun.support.modbus import ModbusException

import logging
logger = logging.getLogger(__name__)

class Type(BaseType):
    "This class is about measuring power and current to the charger."
    help = "Power metering."

class BaseDevice(_BaseDevice):
    def __init__(self, *a,**k):
        self.volt = [0]*3
        self.amp = [0]*3
        self.watt = [0]*3
        self.VA = [0]*3
        self.factor = [0]*3
        self.Wh = [0]*3

        self.volts = 0
        self.amps = 0
        self.amp_max = 0
        self.watts = 0
        self.VAs = 0
        self.Whs = 0
        self.factor_avg = 0

        self.cur_total = 0

        self.charger = None
        self.signal = blinker.Signal()

        super().__init__(*a,**k)

    async def query(self,func,b=None):
        return (await self.bus.query(self.unit,func,b))

    async def floats(self, start,count):
        rr = await self.bus.read_input_registers(start,count*2, unit=self.unit)
        n = len(rr.registers)
        return struct.unpack('>%df'%(n//2),struct.pack('>%dH'%n,*rr.registers))

    async def doubles(self, start,count):
        rr = await self.bus.read_input_registers(start,count*4, unit=self.unit)
        n = len(rr.registers)
        return struct.unpack('>%dd'%(n//4),struct.pack('>%dH'%n,*rr.registers))

    def get_state(self):
        res = super().get_state()
        res['amps'] = self.amp
        res['amp'] = self.amp_max
        res['watts'] = self.watt
        res['watt'] = self.watts
        res['VAs'] = self.VA
        res['VA'] = self.VAs
        res['Whs'] = self.Whs
        res['Wh'] = self.Wh
        res['power_factors'] = self.factor
        res['power_factor'] = self.factor_avg
        res['energy_total'] = self.cur_total
        return res

    def register_charger(self,obj):
        assert self.charger is None
        self.charger = obj
        self.trigger()

    @property
    def in_use(self):
        if self.charger is None:
            return False
        else:
            return self.charger.charging

    @property
    def interval(self):
        if not self.in_use:
            return self.cfg.get('idle',30)
        return super().interval

    async def prepare2(self):
        self.loop_time = 0
        await super().prepare2()
        self.t1 = time()

    async def step1(self):
        await super().step1()
        t2 = time()
        self.loop_time = t2-self.t1
        self.t1 = t2

    async def step2(self):
        logger.debug("%s: %.1f V, %.1f A %s pf %.3f watt %.1f va %.1f sum %.1f",self.name,
            self.volts, self.amps, ','.join('%.2f' % x for x in self.amp),
            self.factor_avg,self.watts,self.VAs,self.cur_total)
        await super().step2()
        self.signal.send(self)

    async def prepare1(self):
        await super().prepare1()
        ### auto mode
        self.bus = await self.cmd.reg.bus.get(self.cfg['bus'])
        self.unit = self.cfg.get('unit',1)
        self.phase1 = int(self.cfg.get('offset',0))
        assert 0 <= self.phase1 <= 2
        self.phase2 = (self.phase1+1)%3
        self.phase3 = (self.phase2+1)%3

class BusDevice(BaseDevice):
    pass

BusDevice.register("config","bus", cls=str, doc="Bus to connect to")
BusDevice.register("config","address", cls=int, doc="This charger's address on the bus")
BusDevice.register("config","power", cls=str, doc="Power supply to use")
BusDevice.register("config","offset", cls=int, doc="phase offset (0,1,2)")

BaseDevice.register("config","idle", cls=float, doc="delay between measurements when not in use")


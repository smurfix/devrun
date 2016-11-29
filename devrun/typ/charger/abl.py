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
from time import time

from . import BaseDevice
from devrun.support.abl import Request,Reply, fADC,RM,RT

import logging
logger = logging.getLogger(__name__)

def pwm(A):
    if A < 6:
        return 0
    if A >= 50:
        return int((A/.25)+640)
    else:
        return int(A/0.06)

class Device(BaseDevice):
    """ABL Sursum chargers"""
    help = """\
This module interfaces to an ABL Sursum-style charger.
"""
    _charging = False
    mode = None
    _A = 0

    async def query(self,func,b=None):
        return (await self.bus.query(self.adr,func,b))

    @property
    def A(self):
        return self._A
    @A.setter
    def A(self,value):
        logger.info("%s: avail %f => %f", self.name,self._A,value)
        assert value == 0 or value >= self.A_min
        assert value <= self.A_max
        self._A = value
        self.trigger.set()

    async def kick_ax(self):
        await asyncio.sleep(10,loop=self.cmd.loop)
        logger.warn("%s: Turn on Ax", self.name)
        await self.query(RT.enter_Ax)

        await asyncio.sleep(5,loop=self.cmd.loop)
        logger.warn("%s: Turn off Ax", self.name)
        await self.query(RT.leave_Ax)

    _charging = False
    charge_start = 0 # EV connected, timestamp
    charge_started = 0 # current started to flow, timestamp
    charge_end = 0 # Charge stopped, timestamp
    charge_init = 0 # meter at beginning, Wh
    charge_exit = 0 # meter at end, Wh
    @property
    def charging(self):
        return self._charging > 1
    @property
    def want_charging(self):
        return self._charging == 1
    @want_charging.setter
    def want_charging(self, val):
        if val and not self._charging:
            self.charge_start = t = time()
            self.charge_init = self.meter.cur_total
            self._charging = 1

    @charging.setter
    def charging(self,val):
        if val:
            if self._charging < 2:
                if not self._charging:
                    self.want_charging = True
                self.charge_started = time()
                self._charging = 2
        else:
            if self._charging:
                self.charge_end = time()
                self.charge_started = 0
                self.charge_exit = self.meter.cur_total
                self._charging = 0

    @property
    def charge_time(self):
        return (time() if self._charging else self.charge_end) - (self.charge_started or self.charge_start)
    @property
    def charge_amount(self):
        return (self.meter.cur_total if self._charging else self.charge_exit) - self.charge_init

    async def get_mode(self):
        mode = await self.query(RT.state)
        if self.mode is not None and mode == self.mode:
            return mode
        while True:
            await asyncio.sleep(0.1,loop=self.cmd.loop)
            mode2 = await self.query(RT.state)
            if mode2 & RM.transient:
                logger.warn("%s: transient %d",self.name,mode)
                continue
            if mode == mode2:
                return mode
            logger.warn("%s: modes %d %d",self.name,mode,mode2)
            mode = mode2

    async def run(self):
        logger.debug("%s: starting", self.name)
        self.trigger = asyncio.Event(loop=self.cmd.loop)

        cfg = self.loc.get('config',{})
        mode = cfg.get('mode','auto')
        if mode == "manual":
            await self.run_manual(cfg)
            return

        if mode != "auto":
            raise ConfigError("Mode needs to be 'auto' or 'manual'")

        ### auto mode
        self.bus = await self.cmd.reg.bus.get(cfg['bus'])
        logger.debug("%s: got bus %s", self.name,self.bus.name)
        self.power = await self.cmd.reg.power.get(cfg['power'])
        logger.debug("%s: got power %s", self.name,self.power.name)
        self.meter = await self.cmd.reg.meter.get(cfg['meter'])
        self.signal = self.meter.signal
        logger.debug("%s: got meter %s", self.name,self.meter.name)
        self.adr = cfg['address']
        self.threshold = cfg.get('threshold',10)
        self.A_max = cfg.get('A_max',32)
        self.A_min = 6
        self.A = self.A_min
        self.power.register_charger(self)
        self.cmd.reg.charger[self.name] = self

        self.mode = await self.get_mode()
        logger.debug("%s: got mode %s", self.name,RM[self.mode])

        if self.mode == RM.manual:
            await self.query(RT.set_auto)

        logger.info("Start: %s",self.name)
        while True:
            self.mode = await self.get_mode()
            if self.mode == RM.manual:
                raise RuntimeError("mode is set to manual??")
            elif self.mode & RM.error:
                raise RuntimeError("Charger %s: error %s", self.name,RM[self.mode])
            else:
                if self.mode in RM.charging:
                    self.charging = True
                elif self.mode in RM.want_charging:
                    self.want_charging = True
                else:
                    self.charging = False
                self.brk = await self.query(RT.brk)

                a = await self.query(RT.input)
                b = await self.query(RT.output)
                c = await self.query(RT.adc_cp_pos)*fADC
                d = await self.query(RT.adc_cp_neg)*fADC
                e = await self.query(RT.adc_cs)*12/1023
                logger.info("M %s I %x O %x + %.02f - %.02f CS %.02f, power %.02f, ch %s brk %s, ch %.01f %.1f",RM[self.mode],a,b,c,d,e, self.A, 'Y' if self.charging else 'N', 'Y' if self.brk else 'N', self.charge_time,self.charge_amount)

                if self.A < self.A_min:
                    if self.charging:
                        logger.warn("%s: min power %f %f",self.name,self.A,self.A_min)
                        await self.query(RT.enter_Ax)
                    if not self.brk:
                        await self.query(RT.set_brk)
                else:
                    await self.query(RT.set_pwm, pwm(self.A))
                    if self.brk:
                        await self.query(RT.clear_brk)
                    if self.mode == RM.Ax:
                        await self.query(RT.leave_Ax)

            try:
                await asyncio.wait_for(self.trigger.wait(), cfg.get('interval',1), loop=self.cmd.loop)
            except asyncio.TimeoutError:
                pass
            else:
                self.trigger.clear()

    async def run_manual(self):
        raise NotImplementedError("Don't know how to do it manually yet")

Device.register("config","mode", cls=str, doc="Operating mode (auto or manual), default auto")
Device.register("config","bus", cls=str, doc="Bus to connect to, mandatory")
Device.register("config","address", cls=int, doc="This charger's address on the bus, mandatory")
Device.register("config","meter", cls=str, doc="Power meter to use, mandatory")
Device.register("config","power", cls=str, doc="Power supply to use, mandatory")
Device.register("config","A_max", cls=float, doc="Maximum allowed current mandatory")
Device.register("config","interval", cls=float, doc="time between checks, default 1sec")
Device.register("config","thresh_wh", cls=float, doc="Wh for charging to have started, default 10")
Device.register("config","thresh_t", cls=float, doc="Timeout for charging to have started, default 30")


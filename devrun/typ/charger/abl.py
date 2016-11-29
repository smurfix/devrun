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

    async def query(self,func,b=None):
        return (await self.bus.query(self.adr,func,b))

    def update_available(self,A):
        logger.info("%s: avail %f => %f", self.name,self.A,A)
        self.A = A
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
        return self._charging
    @charging.setter
    def charging(self,val):
        if val:
            if not self._charging:
                self.charge_start = time()
                self.charge_init = self.meter.cur_total
            if self.charge_started == 0 and self.meter.cur_total - self.charge_init >= self.threshold:
                self.charge_started = time()
                self._charging = True
        else:
            if self._charging:
                self.charge_end = time()
                self.charge_started = 0
                self.charge_exit = self.meter.cur_total
                self._charging = False

    @property
    def charge_time(self):
        return (time() if self._charging else self.charge_end)-self.charge_start
    @property
    def charge_amount(self):
        return (self.meter.cur_total if self._charging else self.charge_exit)-self.charge_init


    async def run(self):
        logger.debug("%s: starting", self.name)
        self._charging = False
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
        self.A = self.A_max
        self.power.register_charger(self)
        self.cmd.reg.charger[self.name] = self

        mode = await self.query(RT.state)
        logger.debug("%s: got mode %s", self.name,RM[mode])

        if mode == RM.manual:
            await self.query(RT.set_auto)

        logger.info("Start: %s",self.name)
        while True:
            while True:
                mode = await self.query(RT.state)
                await asyncio.sleep(0.1,loop=self.cmd.loop)
                mode2 = await self.query(RT.state)
                if mode == mode2:
                    break
                logger.warn("%s: modes %d %d",self.name,mode,mode2)

            if mode == RM.manual:
                raise RuntimeError("mode is set to manual??")
            elif mode & RM.transient:
                logger.warn("%s: transient %d",self.name,mode)
                self.trigger.set()
            elif mode & RM.error:
                raise RuntimeError("Charger %s: error %s", self.name,RM[mode])
            else:
                self.charging = (mode in RM.charging)
                self.brk = await self.query(RT.brk)

                a = await self.query(RT.input)
                b = await self.query(RT.output)
                c = await self.query(RT.adc_cp_pos)*fADC
                d = await self.query(RT.adc_cp_neg)*fADC
                e = await self.query(RT.adc_cs)*12/1023
                logger.info("M %s I %x O %x + %.02f - %.02f CS %.02f, power %.02f, ch %s brk %s, ch %.01f %.1f",RM[mode],a,b,c,d,e, self.A, 'Y' if self.charging else 'N', 'Y' if self.brk else 'N', self.charge_time,self.charge_amount)

                if self.charging:
                    if self.A < self.A_min:
                        logger.warn("%s: min power %f %f",self.name,self.A,self.A_min)
                        await self.query(RT.enter_Ax)
                    else:
                        await self.query(RT.set_pwm, pwm(self.A))
                # not charging
                elif self.A < self.A_min:
                    if not self.brk:
                        await self.query(RT.set_brk)
                    if mode == RM.Ax:
                        await self.query(RT.leave_Ax)
                else:
                    if self.brk:
                        await self.query(RT.clear_brk)
                    await self.query(RT.set_pwm, pwm(self.A))

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
Device.register("config","threshold", cls=float, doc="Wh for charging to have started, default 10")


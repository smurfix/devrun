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

from . import BaseDevice, CM,CA
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

modemap = {
    RM.A: CM.idle,
    RM.B2: CM.starting,
    RM.C: CM.active,
    RM.D: CM.active,
    RM.Bx: CM.done,
    RM.B0: CM.waiting,
    RM.B1: CM.waiting,
    RM.Ax: CM.disabled,

    RM.error: CM.error,
    RM.manual: CM.manual,
    }
brkmap = {
    CM.idle: CM.off,
    }

class Device(BaseDevice):
    """ABL Sursum chargers"""
    help = """\
This module interfaces to an ABL Sursum-style charger.
"""
    _charging = False
    __mode = None
    _A = 0
    last_A = 0
    last_pf = 0
    last_power = 0
    brk = False
    abcde = (0,0,0,0,0)

    async def query(self,func,b=None):
        return (await self.bus.query(self.adr,func,b))

    def get_state(self):
        res = super().get_state()
        res['raw_state'] = RM[self.__mode]
        return res

    @property
    def A(self):
        return self._A
    @A.setter
    def A(self,value):
        if self._A != value:
            logger.debug("%s: avail %f => %f", self.name,self._A,value)
        assert value == 0 or value >= self.A_min
        assert value <= self.A_max
        self._A = value
        self.trigger()

    async def take_action(self,act):
        if act == CA.disable:
            await self.query(RT.enter_Ax)
        elif act == CA.enable: ## or act == CA.thaw:
            await self.query(RT.clear_brk)
            try:
                await self.query(RT.leave_Ax)
            except ValueError:
                pass
        elif act == CA.defer:
            await self.query(RT.set_brk)
        elif act == CA.lock:
            pass
        elif act == CA.unlock:
            pass
        elif act == CA.allow:
            await self.query(RT.clear_brk)
        elif act == CA.unlock:
            await self.query(RT.set_pwm, pwm(self.A))
            await self.query(RT.clear_brk)
        elif act == CA.throw:
            ## defer is called also ##
            await self.query(RT.enter_Ax)
        else:
            raise NotImplementedError(CA[act])
        self.took_action(act)

    async def set_available(self,A):
        await self.query(RT.set_pwm, pwm(self.A))
        self.is_available(A)

    async def read_mode(self):
        mode = await self.query(RT.state)
        if self.__mode is not None and mode == self.__mode:
            return self._mode # current mode
        hits = 0
        while True:
            await asyncio.sleep(0.1,loop=self.cmd.loop)
            mode2 = await self.query(RT.state)
            if mode2 & RM.transient:
                logger.warn("%s: transient %d",self.name,mode)
                continue
            elif mode & RM.error:
                mode = RM.error
            if mode == mode2:
                if mode in modemap or hits >= 10:
                    break
                hits += 1
            logger.warn("%s: modes %d %d",self.name,mode,mode2)
            mode = mode2
        self.__mode = mode
        mode = modemap.get(mode,CM.error)
        if mode in brkmap:
            brk = await self.query(RT.brk)
            if brk:
                mode = brkmap[mode]
        return mode

    async def prepare1(self):
        await super().prepare1()
        cfg = self.cfg
        mode = cfg.get('mode','auto')
        if mode == "manual":
            await self.prep_manual(cfg)
            return
        if mode != "auto":
            raise ConfigError("Mode needs to be 'auto' or 'manual'")

        ### auto mode
        self.bus = await self.cmd.reg.bus.get(cfg['bus'])
        logger.debug("%s: got bus %s", self.name,self.bus.name)
        self.adr = cfg['address']
        self.threshold = cfg.get('threshold',10)
        self.A_min = max(self.A_min,6)
        self.A = self.A_min

        self.mode = await self.read_mode()
        logger.debug("%s: got mode %s", self.name,CM[self.mode])

        if self.mode == CM.manual:
            await self.query(RT.set_auto)

    async def log_me(self):
        await super().log_me()
        p = await self.query(RT.pwm)
        a = await self.query(RT.input)
        b = await self.query(RT.output)
        c = await self.query(RT.adc_cp_pos)*fADC
        c1 = (c+1)//3
        c2 = (c+2)//3
        if (c1 == c2):
            cc = c1*3
        else:
            cc = c
        bb = b
        if self.__mode == RM.A:
            bb |= 0x01
        elif self.__mode in (RM.B2,RM.C):
            bb |= 0x60
        elif self.__mode == RM.Bx:
            bb |= 0x62

        d = await self.query(RT.adc_cp_neg)*fADC
        if (d < 1):
            dd = 0
        elif (d > 11):
            dd = 12
        else:
            dd = d
        e = await self.query(RT.adc_cs)*12/1023
        if self.abcde[:5] != (p,a,bb,cc,dd) or abs(self.abcde[5]-e)>0.2:
            logger.info("%s: M %s I %x O %x + %.02f - %.02f CS %.02f pwm %d",self.name, RM[self.__mode],a,b,c,d,e,p)
            self.abcde = (p,a,bb,cc,dd,e)

    async def step1(self):
        await super().step1()
        if self.mode == CM.manual:
            raise RuntimeError("mode is set to manual??")

        if self.mode == CM.active and self.meter.amp_max*self.meter.factor_avg > 0.5:
            self.mode = CM.charging

        await self.dispatch_actions()

    async def prep_manual(self):
        raise NotImplementedError("Don't know how to do it manually yet")

Device.register("config","mode", cls=str, doc="Operating mode (auto or manual), default auto")
Device.register("config","bus", cls=str, doc="Bus to connect to, mandatory")
Device.register("config","address", cls=int, doc="This charger's address on the bus, mandatory")
Device.register("config","thresh_wh", cls=float, doc="Wh for charging to have started, default 10")
Device.register("config","thresh_t", cls=float, doc="Timeout for charging to have started, default 30")


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
from random import Random

from . import BaseDevice,CM,CA
from devrun.support.abl import Request,Reply, fADC,RM,RT

import logging
logger = logging.getLogger(__name__)

ModeMap = {
    CM.unknown:{CM.off:2}, # newly initialized
    CM.error:{CM.off:5,CM.disabled:5}, # not working due to error
    CM.disabled:{CM.off:2}, # permanently not working A'
    CM.off:{CM.waiting:5}, # no power available, no car; >idle due to power control
    CM.idle:{CM.starting:5}, # power available, no car A
    CM.done:{CM.idle:3,CM.starting:6}, # charging done Bx
    CM.waiting:{}, # car but no power B1(+defer): >starting on power
    CM.starting:{CM.active:3}, # waiting for charge to enable B2
    CM.active:{CM.done:30}, # charging but no measured load C, >charging on power
    CM.charging:{CM.done:40}, # charging
}

class Device(BaseDevice):
    """Random chargers"""
    help = """\
This module implements a dummy charger which is randomly turning itself on and off.
"""
    _new_mode = CM.unknown

    @property
    def new_mode(self):
        return self._new_mode
    @new_mode.setter
    def new_mode(self,m):
        if self._new_mode == CM.unknown or m == CM.unknown or self._new_mode > m:
            self._new_mode = m
        else:
            logger.info("%s: ignore mode change %s to %s due to %s",
                self.name,CM[self._mode],CM[m],CM[self._new_mode])

    async def prepare1(self):
        await super().prepare1()
        self.rand = Random()

        cfg = self.loc.get('config',{})
        self.signal = self.meter.signal
        logger.debug("%s: got meter %s", self.name,self.meter.name)
        self.threshold = cfg.get('threshold',10)
        self.A_min = self.A_max/5
        self.A = self.A_min

    async def take_action(self,act):
        logger.info("%s: faking action: %s in %s", self.name,CA[act],CM[self._mode])

        if act == CA.disable:
            self.new_mode = CM.disabled
        elif act == CA.throw:
            self.new_mode = CM.disabled
        elif act == CA.lock:
            pass
        elif act == CA.defer:
            self.deferred = True
        elif act == CA.enable:
            if self._mode == CM.disabled:
                self.new_mode = CM.idle if self._A > 0 else CM.off
        elif act == CA.unlock:
            pass
        elif act == CA.allow:
            if self._mode == CM.waiting:
                self.new_mode = CM.starting
            elif self._mode == CM.off:
                self.new_mode = CM.idle

        self.took_action(act)

    async def set_available(self,A):
        if A > 0:
            if self._mode == CM.off:
                self.new_mode = CM.idle
        else:
            if self._mode == CM.idle:
                self.new_mode = CM.off
        self.is_available(A)

    async def read_mode(self):
        if self.new_mode != CM.unknown:
            m,self.new_mode = self.new_mode,CM.unknown
            return m
        if self._mode == CM.disabled and self.disabled:
            return self._mode
        for k,v in ModeMap.get(self._mode,{}).items():
            if not self.rand.randrange(v):
                return k
        return self._mode

    async def step1(self):
        await super().step1()
        if self._mode == CM.active and self.meter.amp_max>0.1:
            self.mode = CM.charging
        await self.dispatch_actions()

    async def run_manual(self):
        raise NotImplementedError("Don't know how to do it manually yet")

Device.register("config","meter", cls=str, doc="Power meter to use, mandatory")
Device.register("config","power", cls=str, doc="Power supply to use, mandatory")
Device.register("config","A_max", cls=float, doc="Maximum allowed current, mandatory")
Device.register("config","interval", cls=float, doc="time between checks, default 1sec")
Device.register("config","up", cls=int, doc="1-in-n probability for starting to charge, default 3")
Device.register("config","down", cls=int, doc="1-in-n probability for stopping, default 5")


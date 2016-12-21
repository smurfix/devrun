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

import blinker
from time import time

from devrun.typ import BaseType
from devrun.device import BaseDevice as _BaseDevice

import logging
logger = logging.getLogger(__name__)

class Type(BaseType):
    "This class is about measuring power and current to the charger."
    help = "Power metering."

class BaseDevice(_BaseDevice):
    def __init__(self, *a,**k):
        self.amp = [0]*3
        self.watt = [0]*3
        self.VA = [0]*3
        self.factor = [0]*3

        self.amps = 0
        self.amp_max = 0
        self.watts = 0
        self.VAs = 0
        self.factor_avg = 0

        self.cur_total = 0

        self.charger = None
        self.signal = blinker.Signal()

        super().__init__(*a,**k)

    def register_charger(self,obj):
        assert self.charger is None
        self.charger = obj
        self.trigger()

    @property
    def interval(self):
        if not self.in_use:
            return self.cfg.get('idle',30)
        return super().interval

    async def prepare1(self):
        await super().prepare1()
        self.power = await self.cmd.reg.power.get(self.cfg['power'])

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
        logger.debug("%s: amp %.1f %s pf %.3f watt %.1f va %.1f sum %.1f",self.name,
            self.amps, ','.join('%.2f' % x for x in self.amp),
            self.factor_avg,self.watts,self.VAs,self.cur_total)
        await super().step2()
        self.signal.send(self)

BaseDevice.register("config","idle", cls=float, doc="delay between measurements when not in use")
BaseDevice.register("config","power", cls=str, doc="Power supply to use")


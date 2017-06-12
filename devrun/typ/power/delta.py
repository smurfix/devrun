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

from .limit import Device as BaseDevice

import logging
logger = logging.getLogger(__name__)

class Device(BaseDevice):
    """Power limit"""
    help = """\
This module implements limiting a group of chargers to some maximum
current, subject to availability.
"""

    async def prepare1(self):
        await super().prepare1()
        self.P_max = self.cfg['P_max']*1000
        self.dampen = self.cfg.get('dampen',0.1)
        assert 0 < self.dampen < 1, "Damping factor must be between zero and one"
        self.meter = await self.cmd.reg.meter.get(self.cfg['meter'])
        self.meter.register_charger(self)
        self.meter.signal.connect(self.has_values)
        self.last_w_at = 0

    @property
    def A_avail(self):
        t = time()
        if self.last_w_at and self.meter.cur_total:
            if t - self.last_w_at >= self.meter.interval:
                P_now = (self.meter.cur_total - self.last_w) / (t - self.last_w_at) * 3600
                self.P_now = P_now*self.dampen + self.P_now*(1-self.dampen)
            else:
                t = 0 # too fast, do not update
                P_now = self.P_now
        else:
            self.P_now = P_now = self.meter.watts
        if t:
            self.last_w_at = t
            self.last_w = self.meter.cur_total

        Aavail = (self.P_max - self.P_now) / self.meter.volts / 3
        if t:
            print("*** avail:",Aavail,self.A_max,P_now,self.P_now,self.meter.watts)
        return min(Aavail,self.A_max)

Device.register("config","A_max", cls=float, doc="Maximum allowed current (A), required")
Device.register("config","P_max", cls=float, doc="Maximum allowed power (kWh), required")
Device.register("config","dampen", cls=float, doc="Moving average for power")


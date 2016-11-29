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

from . import BaseDevice
from devrun.support.abl import Request,Reply, fADC,RM,RT

import logging
logger = logging.getLogger(__name__)

class Device(BaseDevice):
    """Power limit"""
    help = """\
This module implements limiting a group of chargers to some maximum
current.
"""

    @property
    def charging(self):
        for k in self.chargers.values():
            if k.charging:
                yield k
    @property
    def not_charging(self):
        for k in self.chargers.values():
            if not k.charging:
                yield k

    def update_available(self):
        ## TODO: consider the three phases separately

        A_max = 0 # if everybod charges maximally
        A_min = 0 # if everybod charges minimally
        Aprio = 0 # unassigned capacity, priority
        Adelta = 0 # unassigned capacity
        Aidle = 0 # requirements of idle stations
        n_p = 0 # number of priority stations
        n_c = 0 # number of charging stations
        n_nc = 0 # number of non-charging stations

        # first, check current usage
        for k in self.charging:
            A_max += k.A_max
            A_min += k.A_min
            if k.charge_time <= self.ramp_up:
                Am = k.A_max
                Aprio += Am-k.A_min
                n_p += 1
            else:
                Am = k.A_min
                for n in (0,1,2):
                    A = min(k.meter.amp[n]*self.headroom, k.A_max)
                    Am = max(Am,A)
                Adelta += Am-k.A_min
                n_c += 1

        # sum requirements of idle stations
        for k in self.not_charging:
            n_nc += 1
            Aidle += k.A_min
        logger.info("max %.1f, min %.1f, delta %.1f, idle %.1f", A_max,A_min,Adelta,Aidle)

        # Emergency: we can't even handle all charging stations
        if A_min > self.A_max:
            for k in sorted(self.charging, key=lambda x:-x.meter.amps):
                if A_min > k.A_min:
                    A_min -= k.A_min
                    k.update_available(k.A_min)
                else:
                    k.update_available(0)
            for k in self.not_charging:
                k.update_available(0)
            return

        for k in self.charging:
            k.update_available(max(k.A_min,min(k.A_max,k.meter.amp[n]*self.headroom)))
        for k in self.not_charging:
            k.update_available(k.A_min)
        return
        Aavail = self.A_max
        if Aavail > Adelta:
            # we can assign max power to every station
            for k in self.charging:
                k.update_available(k.A_max)
        else:
            pass

        if Aidle > self.A_max:
            # we can give all idle stations enough for min power
            pass
        else:
            pass

        if n_c == 0:
            Afree = self.A_max
        elif A_max <= self.A_max:
            for k in self.charging:
                k.update_available(k.A_max)
            Afree = self.A_max - A_max
        elif A_min >= self.A_max:
            # OWCH
            Acom = self.A_max
            for k in self.charging:
                if k.A_min <= Acom:
                    k.update_available(k.A_min)
                    Acom -= k.A_min
                else:
                    k.update_available(0)
            Afree = 0
        else: # distribute
            f=self.A_max/A_max
            assert f<1
            for k in self.charging:
                k.update_available(k.A_max*f)
            Afree = 0

        # TODO: check meters for actual power use

        for k in self.not_charging:
            if Afree/n_nc >= k.A_min:
                k.update_available(k.A_min)
            else:
                k.update_available(0)

    def has_values(self, obj):
        assert obj.name in self.chargers
        self.update_available()

    def register_charger(self, obj):
        self.q.put_nowait(('reg',obj))

    async def run(self):
        cfg = self.loc.get('config',{})
        self.A_max = cfg['A_max']
        self.ramp_up = cfg.get('ramp_up',5*60)
        self.headroom = cfg.get('headroom',1.1)
        self.chargers = {}
        self.q = asyncio.Queue()
        self.cmd.reg.power[self.name] = self
        logger.info("Start: %s",self.name)

        while True:
            cmd,obj = await self.q.get()
            if cmd == 'reg':
                logger.debug("Reg: charger %s",obj.name)
                self.chargers[obj.name] = obj
                obj.signal.connect(self.has_values)

Device.register("config","A_max", cls=float, doc="Maximum allowed current, required")
Device.register("config","ramp_up", cls=float, doc="charge time with full power, default 5min")
Device.register("config","headroom", cls=float, doc="additional current limit, default 1.1 times current usage")


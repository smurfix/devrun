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

class ZeroPrio:
    """Make sure that every charger is affected"""
    def applies(self,c,a):
        """Check if this level affects this charger.
            @a is the absolute available current."""
        return True

    def requires(self,c,a):
        """At this priority, return what the charger @c requires.
            @a is absolute available current at this point.
            The returned value must not include any lower prio levels!"""
        return 0

    def set(self,c,a,f,base):
        """Return the current to use from this level.
            @a is this level's total available excess current, @f the
            factor of the value returned by @requires that this charger may
            use."""
        a = (self.requires(c,a)-base)*f+base
        if a < c.A_min:
            return 0
        return a

class MinPrio (ZeroPrio):
    """Make sure that continuing charging is possible."""
    def applies(self,c,a):
        return c.charging

    def requires(self,c,a):
        if a>=c.A_min:
            return c.A_min
        return 0

    def set(self,c,a,f,base):
        if a>=c.A_min:
            return c.A_min
        return 0

class MinWant (MinPrio):
    """Add min load for waiting chargers"""
    def applies(self,c,a):
        return c.want_charging

class InitCharging (ZeroPrio):
    """Initial ramp-up for newly charging vehicles"""
    def applies(self,c,a):
        return c.charging and c.charge_time < c.power.ramp_up
    def requires(self,c,a):
        return c.A_max

class FeedBased (ZeroPrio):
    """Limit the charger to some multiple of what it actually pulls"""
    def applies(self,c,a):
        return c.charging and c.charge_time >= c.power.ramp_up
    def requires(self,c,a):
        Am = c.A_min
        for n in (0,1,2):
            Am = max(Am, min(c.meter.amp[n]*c.power.headroom, c.A_max))
        return Am

class AddIdle (MinPrio):
    """Activate some currently-non-charging stations"""
    def applies(self,c,a):
        return c.useful and not c.charging and not c.want_charging

class FullPower (FeedBased):
    """proportional fullpower"""
    def requires(self,c,a):
        return c.A_max

class FullPower2 (FullPower):
    """absolute fullpower"""
    def set(self,c,a,f,base):
        a += base
        if a < c.A_min:
            return 0
        if a > c.A_max:
            return c.A_max
        return a

class FullPowerWaiting (FullPower):
    def applies(self,c,a):
        return c.want_charging
    def requires(self,c,a):
        return c.A_max

class FullPowerIdle (FullPowerWaiting):
    def applies(self,c,a):
        return not c.charging and not c.want_charging

prio = (ZeroPrio,MinPrio, InitCharging,MinWant, FeedBased,AddIdle,FullPower,FullPower2,
        FullPowerWaiting,FullPowerIdle)

class Device(BaseDevice):
    """Power limit"""
    help = """\
This module implements limiting a group of chargers to some maximum
current.
"""

    @property
    def charging(self):
        for k in self.chargers:
            if k.charging:
                yield k
    @property
    def want_charging(self):
        for k in self.chargers:
            if k.want_charging and not k.charging:
                yield k
    @property
    def not_charging(self):
        for k in self.chargers:
            if not k.charging and not k.want_charging:
                yield k

    @property
    def A_avail(self):
        return self.A_max

    def update_available(self):
        """Update my chargers' available current."""
        ## TODO: consider the three phases separately

        # We have this much current, total
        Aavail = self.A_avail
        print()

        # Clear the power assigned to the chargers
        for k in self.chargers:
            k.__assigned = 0

        for p in self.prio:
            if Aavail <= 0:
                break

            # collect power demands at this level
            Ahere = 0
            for k in self.chargers:
                if not p.applies(k,Aavail):
                    continue
                A = p.requires(k,Aavail)-k.__assigned
                if A > 0:
                    Ahere += A
                    print("req",k,Aavail,'=',A)
            
            # check how much chargers actually do use, given the factor
            Aassigned = 0
            print("f",p.__class__.__name__,Aavail,Ahere)
            if Aavail < Ahere:
                f = Aavail/Ahere # less than 100% available
            else:
                f = 1
            for k in self.chargers:
                if not p.applies(k,Aavail):
                    continue
                A = p.set(k,Aavail,f,k.__assigned)
                print("set",k,"from",k.__assigned,"with",Aavail,f,'=',A)
                if A > k.__assigned:
                    A -= k.__assigned
                    if A > Aavail:
                        A = Aavail
                    k.__assigned += A
                    assert k.__assigned <= k.A_max,(k,p,A,Aavail,f)
                    Aavail -= A
        # First, reduce.
        for k in self.chargers:
            if k.A > k.__assigned:
                k.A = k.__assigned
        # Then, increase
        for k in self.chargers:
            if k.A < k.__assigned:
                k.A = k.__assigned

    def has_values(self, obj):
        assert obj.name in self._chargers
        self.update_available()

    def register_charger(self, obj):
        self.q.put_nowait(('reg',obj))

    @property
    def chargers(self):
        return self._chargers.values()

    async def prepare1(self):
        await super().prepare1()
        self.prio = tuple(p() for p in prio)
        self.A_max = self.cfg['A_max']
        self.ramp_up = self.cfg.get('ramp_up',20) ## 5*60
        self.headroom = self.cfg.get('headroom',1.1)
        self._chargers = {}
        self.q = asyncio.Queue()

    async def run(self):
        await self.prepare1()
        await self.prepare2()

        while True:
            cmd,obj = await self.q.get()
            if cmd == 'reg':
                logger.debug("Reg: charger %s",obj.name)
                self._chargers[obj.name] = obj
                obj.signal.connect(self.has_values)

Device.register("config","A_max", cls=float, doc="Maximum allowed current, required")
Device.register("config","ramp_up", cls=float, doc="charge time with full power, default 5min")
Device.register("config","headroom", cls=float, doc="lower current limit, default 1.1 times current usage")


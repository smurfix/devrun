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
    """Random chargers"""
    help = """\
This module implements a dummy charger which is randomly turning itself on and off.
"""
    _charging = 0
    _A = 0
    ready = False
    last_A = 0
    last_pf = 0
    last_power = 0

    def get_state(self):
        res = super().get_state()
        res['charging'] = self.charging
        res['charge_Wh'] = self.charge_amount
        res['charge_sec'] = self.charge_time
        res['connected'] = self.charging or self.want_charging
        res['on_hold'] = self.A == 0
        if res['connected']:
            res['A_avail'] = self.A
        if res['charging']:
            res['power'] = self.meter.watts
            res['amp'] = self.meter.amp_max
            res['power_factor'] = self.meter.factor_avg
        return res

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

    def has_meter_value(self):
        self.ready = True

    async def run(self):
        logger.debug("%s: starting", self.name)
        self.trigger = asyncio.Event(loop=self.cmd.loop)
        self.rand = Random()

        cfg = self.loc.get('config',{})

        ### auto mode
        self.power = await self.cmd.reg.power.get(cfg['power'])
        logger.debug("%s: got power %s", self.name,self.power.name)
        self.meter = await self.cmd.reg.meter.get(cfg['meter'])
        self.signal = self.meter.signal
        logger.debug("%s: got meter %s", self.name,self.meter.name)
        self.threshold = cfg.get('threshold',10)
        self.A_max = cfg.get('A_max',32)
        self.A_min = self.A_max/5
        self.A = self.A_min
        self.power.register_charger(self)
        self.meter.register_charger(self)
        self.cmd.reg.charger[self.name] = self
        self.p_up = cfg.get('up',3)
        self.p_down = cfg.get('down',5)

        logger.info("Start: %s",self.name)
        while True:
            send_alert = False
            if self._charging < 2 and self.A >= self.A_min and not self.rand.randrange(self.p_up):
                if self._charging:
                    self.charging=True
                else:
                    self.want_charging=True
                send_alert = True

            elif self._charging and not self.rand.randrange(self.p_down):
                self.charging=False
                send_alert = True
            
            if self.A < self.A_min:
                if self.charging:
                    logger.warn("%s: min power %f %f",self.name,self.A,self.A_min)
                    self.charging = False
            if self.charging and not send_alert:
                if self.last_A != self._A and abs(self.last_A-self._A)/max(self.last_A,self._A) > 0.05:
                    send_alert = True
                elif self.last_pf != self.meter.factor_avg and abs(self.last_pf-self.meter.factor_avg)/max(self.last_pf,self.meter.factor_avg) > 0.05:
                    send_alert = True
                elif self.last_power != self.meter.watts and abs(self.last_power-self.meter.watts)/max(self.last_power,self.meter.watts) > 0.05:
                    send_alert = True

            logger.info("%s: Amp %.02f, ch %s ch %.01f %.1f",self.name, self.A, 'Y' if self.charging else 'W' if self.want_charging else 'N', self.charge_time,self.charge_amount)
            if send_alert:
                await self.cmd.amqp.alert("update.charger", _data=self.get_state())
                self.last_A = self._A
                self.last_pf = self.meter.factor_avg
                self.last_power = self.meter.watts

            try:
                await asyncio.wait_for(self.trigger.wait(), cfg.get('interval',1), loop=self.cmd.loop)
            except asyncio.TimeoutError:
                pass
            else:
                self.trigger.clear()

    async def run_manual(self):
        raise NotImplementedError("Don't know how to do it manually yet")

Device.register("config","meter", cls=str, doc="Power meter to use, mandatory")
Device.register("config","power", cls=str, doc="Power supply to use, mandatory")
Device.register("config","A_max", cls=float, doc="Maximum allowed current, mandatory")
Device.register("config","interval", cls=float, doc="time between checks, default 1sec")
Device.register("config","up", cls=int, doc="1-in-n probability for starting to charge, default 3")
Device.register("config","down", cls=int, doc="1-in-n probability for stopping, default 5")


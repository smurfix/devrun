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
This module implements talking to a charger.

"""

import asyncio
import blinker

from devrun.typ import BaseType
from devrun.device import BaseDevice as _BaseDevice
from devrun.support import rev
from time import time

from logging import getLogger
logger = getLogger(__name__)

@rev
class CM:
    """Charger modes"""
    unknown=0 # newly initialized
    error=1 # not working due to error
    manual=2 # manual mode
    disabled=3 # permanently not working A'
    off=10 # no power available, no car A+lock
    idle=11 # power available, no car A
    NEW=20 # threshold for connecting a new car
    done=21 # charging done Bx
    OLD=25 # threshold for reporting as disconnected
    waiting=26 # car but no power B1(+lock)
    starting=27 # waiting for car to start B2
    active=30 # charging but no measured load C
    charging=31 # charging and measured load
    _inf=999

    powered={idle,done,starting,active,charging},

@rev
class CA:
    """Action for the charger to take"""
    none=0 # no action
    disable=1 # permanently
    throw=2 # temporary disable while charging
    lock=3 # don't allow connecting a car (physically)
    defer=4 # no power available

    ON=10 # threshold for enabling things

    enable=11 # turn off 'disable'
    unlock=13 # allow connecting a car
    allow=14 # power is available
    

class Type(BaseType):
    "This class is about chargers."
    help = "Charger."

class BaseDevice(_BaseDevice):
    """Common methods for chargers"""

    name = display_name = "‹starting up›"
    _mode = last_mode = force_mode = CM.unknown
    _A = 0
    A_min = 10 # override, possibly

    A_sent = 0 # last set A value

    restart = False # force charger off
    powered = False # power available?

    # used for triggering an alert message
    last_A = 0
    last_pf = 0
    last_power = 0
    send_alert = False

    # status
    charge_start = 0 # EV connected, timestamp
    charge_started = 0 # current started to flow, timestamp
    charge_ended = 0 # current stopped flowing
    charge_end = 0 # Charge stopped, timestamp
    charge_init = 0 # meter at beginning, Wh
    charge_exit = 0 # meter at end, Wh

    # state flags. See CA.
    disabled=False
    thrown=False # cleared when throw succeeds
    locked=False
    deferred=None

    want_lock=False
    want_disable=False

    def lock(self):
        self.want_lock = True
        self.trigger()
    def unlock(self):
        self.want_lock = False
        self.trigger()
    def disable(self):
        self.want_disable = True
        self.trigger()
    def enable(self):
        self.want_disable = False
        self.trigger()

    def took_action(self,act):
        """Call to update flags after doing something"""
        if act == CA.disable:
            self.disabled = True
        elif act == CA.throw:
            self.thrown = True
            self.deferred = True
        elif act == CA.lock:
            self.locked = True
        elif act == CA.defer:
            self.deferred = True
        elif act == CA.enable:
            self.disable = False
        elif act == CA.unlock:
            self.locked = False
        elif act == CA.allow:
            self.deferred = False

    async def take_action(self,act):
        """Tell the charger to do something. Need to override. Must call took_acction()"""
        raise NotImplementedError("Need to override take_action!" % self.__class__.__name__)

    async def set_available(self,A):
        """update available amp. need to override. Must call is_available"""
        raise NotImplementedError("Need to override set_available!" % self.__class__.__name__)

    def is_available(self,A):
        logger.debug("%s: available: %.02f => %.02f",self.name,self.A_sent,A)
        self.A_sent = A

    async def read_mode(self):
        """Get the charger's current mode. Need to override."""
        raise NotImplementedError("Need to override read_mode!" % self.__class__.__name__)

    def get_state(self):
        res = super().get_state()
        res['display_name'] = self.display_name
        res['state'] = CM[self._mode]
        res['charge_Wh'] = self.charge_amount
        res['charge_sec'] = self.charge_time
        res['charging'] = self._mode >= CM.charging
        res['connected'] = self._mode >= CM.NEW
        res['on_hold'] = self.A == 0
        res['amp_avail'] = self.A
        if res['charging']:
            res['power'] = self.meter.watts
            res['amp'] = self.meter.amp_max
            res['power_factor'] = self.meter.factor_avg
        return res

    @property
    def mode(self):
        return self._mode
    @mode.setter
    def mode(self,mode):
        if self._mode == mode:
            return
        self.send_alert = True
        self.meter.trigger()
        if self._mode < CM.NEW and mode > CM.NEW:
            self.charge_start = self.charge_end = time()
            self.charge_started = self.charge_ended = 0
            self.charge_init = self.charge_exit = self.meter.cur_total
        elif self._mode > CM.OLD and mode < CM.OLD:
            self.charge_end = time()
            self.charge_exit = self.meter.cur_total
        if self._mode < CM.charging and mode >= CM.charging:
            self.charge_started = time()
        elif self._mode >= CM.charging and mode < CM.charging:
            self.charge_ended = time()
        self._mode = mode

    @property
    def A(self):
        return self._A
    @A.setter
    def A(self,value):
        logger.debug("%s: avail %f => %f", self.name,self._A,value)
        assert value == 0 or value >= self.A_min
        assert value <= self.A_max
        self._A = value
        self.trigger()

    @property
    def charge_time(self):
        return (time() if self._mode > CM.OLD else self.charge_end) - (self.charge_started or self.charge_start)
    @property
    def charge_amount(self):
        return (self.meter.cur_total if self._mode > CM.OLD else self.charge_exit) - self.charge_init

    @property
    def charging(self):
        return self._mode >= CM.active
    @property
    def want_charging(self):
        return self._mode > CM.NEW and self._mode < CM.active

    async def dispatch_actions(self):
        """State machine. Must be called from .step()"""
        if self._mode < CM.disabled:
            return

        if not self.thrown:
            if self.want_disable:
                if not self.disabled:
                    await self.take_action(CA.disable)
            else:
                if self.disabled:
                    await self.take_action(CA.enable)

        if self._mode == CM.disabled:
            if self.disabled:
                self.thrown = False
            elif self.thrown:
                self.thrown = False
                await self.take_action(CA.enable)

        ## Power available?
        if self._A == 0: # no
            if self.deferred is not True:
                if self._mode > CM.NEW: # throw off
                    await self.take_action(CA.throw)
                await self.take_action(CA.defer)
        else: # power available
            if self.A_sent > self._A or self.A_sent < self._A*0.98:
                # don't update for a more-than-modest increase
                await self.set_available(self._A)
            if self.deferred is not False:
                await self.take_action(CA.allow)

        ## May connect a car?
        if self.want_lock:
            if not self.locked:
                await self.take_action(CA.lock)
        else:
            if self.locked:
                await self.take_action(CA.unlock)
    @property
    def useful(self):
        """true if this charger is of any use.
            If not, don't bother allocating power to it"""
        if self._mode > CM.NEW:
            return True
        if self._mode < CM.disabled or self.disabled:
            return False

    async def log_me(self):
        logger.debug("%s:%s Amp %.02f, ch %.01f %.1f",self.name, CM[self._mode],self.A, self.charge_time,self.charge_amount)

    async def prepare1(self):
        await super().prepare1()
        cfg = self.cfg

        self.display_name = cfg.get('display',self.name)
        self.power = await self.cmd.reg.power.get(cfg['power'])
        self.meter = await self.cmd.reg.meter.get(cfg['meter'])
        control = cfg.get('control',None)
        if control is not None:
            control = self.cmd.reg.control.get(control)
        self.control = control
        self.signal = self.meter.signal
        
        self.A_max = cfg.get('A_max',32)

    async def prepare2(self):
        self.meter.register_charger(self)
        self.power.register_charger(self)
        if self.control:
            self.control.register_charger(self)
        self.send_alert = True
        await super().prepare2()

    async def step1(self):
        await super().step1()
        self.mode = await self.read_mode()

    async def step2(self):
        if not self.send_alert and self._mode >= CM.charging:
            if self.last_A != self._A and abs(self.last_A-self._A)/max(self.last_A,self._A) > 0.05:
                self.send_alert = True
            elif self.last_pf != self.meter.factor_avg and abs(self.last_pf-self.meter.factor_avg)/max(self.last_pf,self.meter.factor_avg) > 0.05:
                self.send_alert = True
            elif self.last_power != self.meter.watts and abs(self.last_power-self.meter.watts)/max(self.last_power,self.meter.watts) > 0.05:
                self.send_alert = True

        if self.send_alert or self.last_alert+5 < time():
            # the 5 is hardcoded: 0.1 minutes are six seconds
            self.last_alert = time()

            await self.log_me()
            await self.cmd.amqp.alert("update.charger", _data=self.get_state())
            self.last_A = self._A
            self.last_pf = self.meter.factor_avg
            self.last_power = self.meter.watts
            self.send_alert = False
        await super().step2()

BaseDevice.register("config","display", cls=str, doc="Name to show in the GUI")
BaseDevice.register("config","meter", cls=str, doc="Power meter to use, mandatory")
BaseDevice.register("config","control", cls=str, doc="Power meter to use, mandatory")
BaseDevice.register("config","power", cls=str, doc="Power supply to use, mandatory")
BaseDevice.register("config","A_max", cls=float, doc="Maximum allowed current, mandatory")

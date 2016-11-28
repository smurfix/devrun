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
        Amax = 0
        Amin = 0
        Aused = [0,0,0]
        n_c = 0
        for k in self.charging:
            Amax += k.A_max
            Amin += k.A_min
            for n in (1,2,3):
                Aused[n-1] += k.meter.amps[n]
            n_c += 1
        Aused = max(Aused)

        if n_c == 0:
            Afree = self.A_max
        elif Amax <= self.A_max:
            for k in self.charging:
                k.update_available(k.A_max)
            Afree = self.A_max - Amax
        elif Amin >= self.A_max:
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
            f=self.A_max/Amax
            assert f<1
            for k in self.charging:
                k.update_available(k.A_max*f)
            Afree = 0

        # TODO: check meters for actual power use

        for k in self.not_charging:
            if Afree >= k.A_min:
                k.update_available(k.A_min)
                # TODO: free more, if possible
                Afree -= k.A_min
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

Device.register("config","A_max", cls=float, doc="Maximum allowed current")


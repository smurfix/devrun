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

class Device(BaseDevice):
    """ABL Sursum chargers"""
    help = """\
This module interfaces to an ABL Sursum-style charger.
"""

    async def query(self,func,b=None):
        return (await self.bus.query(self.adr,func,b))

    async def run(self):
        cfg = self.loc.get('config',{})
        mode = cfg.get('mode','auto')
        if mode == "manual":
            await self.run_manual(cfg)
            return

        if mode != "auto":
            raise ConfigError("Mode needs to be 'auto' or 'manual'")

        ### auto mode
        self.bus = self.cmd.reg.bus.get(cfg['bus'])
        self.power = self.cmd.reg.bus.get(cfg['power'])
        self.meter = self.cmd.reg.bus.get(cfg['meter'])
        self.adr = cfg['address']
        self.A_max = cfg.get('A_max',32)

        while True:
            mode = await self.query(RT.state)
            if mode == RM.manual:
                await self.query(RT.set_auto)
            if mode > RT.firstErr:
                raise RuntimeError("Charger %s: error %s", self.name,RT[mode])
            avail = self.power.available(self.name)
            limited = await self.query(RT.break)
            if limited:
                await self.query(RT.clear_break)
                if avail >= 6:
                    await self.query(RT.set_pwm, avail*fADC)
            else:
                if avail < 6:
                    await self.query(RT.set_break)


            mode = await self.query(RT.state)
            if mode == RM.manual:
                raise RuntimeError("mode is set to manual??")

            
    async def run_manual(self):
        raise NotImplementedError("Don't know how to do it manually yet")

Device.register("config","mode", cls=str, doc="Operating mode (auto or
manual)")
Device.register("config","bus", cls=str, doc="Bus to connect to")
Device.register("config","address", cls=int, doc="This charger's address on the bus")
Device.register("config","meter", cls=str, doc="Power meter to use")
Device.register("config","power", cls=str, doc="Power supply to use")
Device.register("config","A_max", cls=float, doc="Maximum allowed current")


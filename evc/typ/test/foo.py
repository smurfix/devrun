# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This file is part of evc, a comprehensive controller and monitor for
## chargers of electric vehicles.
##
## evc is Copyright © 2016 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.rst` for details,
## including optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP

import asyncio
import sys

#from evc.etcd.types import EvcDevice, EtcFloat
#from evc.typ import Verified
from evc.device import BaseDevice

class Device(BaseDevice):
    """Test device for annoying people"""
    help = """\
This is the FooTest device.
It prints 'Foo' every second, or however often you set it to.
"""
    
    def verify_interval(self, v):
        if v <= 0:
            raise ParamError(k,'must be greater than zero')

    async def run(self):
        while True:
            await asyncio.sleep(self.loc.get('config',{}).get('interval',1), loop=self.cmd.loop)
            print("Ping from foo."+self.name)

#Device.register("config","interval", cls=EtcFloat, doc="Interval between 'foo' pings")


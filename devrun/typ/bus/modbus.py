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
from pymodbus.client.async_asyncio import ReconnectingAsyncioModbusTcpClient
from pymodbus.client.common import ModbusClientMixin

from . import BaseDevice

import logging
logger = logging.getLogger(__name__)

class Device(BaseDevice, ModbusClientMixin):
    """ModBus link"""
    help = """\
This is a link to Modbus.

You can connect to a local serial interface,
or to a remote modbus gateway.
"""

    proto = None

    async def run(self):
        self.end = asyncio.Event()
        logger.info("Start: %s",self.name)

        try:
            cfg = self.loc.get('config',{})
            host = cfg['host']
            if not host:
                raise KeyError(host)
        except KeyError:
            raise ConfigError("You need to specify a host")
        if host[0] == '/': # local device
            raise NotImplementedError("local modbus")

        else:
            if ':' in host:
                host,port=host.split(':')
            else:
                port = 502

            self.proto = ReconnectingAsyncioModbusTcpClient()
            await self.proto.start(host,port)

        await self.end.wait()

        logger.info("Stop: %s",self.name)
        self.proto.stop()

    def stop(self):
        logger.info("Stopping: %s",self.name)
        self.event.set()

    async def execute(self,request):
        return (await self.proto.protocol.execute(request))


Device.register("config","host", cls=str, doc="Host[:port] to connect to, or /dev/serial")


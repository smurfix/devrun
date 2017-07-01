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
from devrun.support.modbus import ModbusException
from pymodbus.client.async import ModbusClientProtocol
from pymodbus.client.common import ModbusClientMixin
from pymodbus.pdu import ExceptionResponse

from . import BaseDevice
from devrun.support.timing import Stats
from devrun.support.modbus import AioModbusClientProtocol

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

    def _restart_done(self,t):
        try:
            r = t.result()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception("%s: Failed to reconnect", self.name)

    async def _restart(self):
        dly = 1
        logger.info("%s: Restarting", self.name)
        while True:
		await self.start_client()
            except asyncio.CancelledError:
                return
            except Exception as exc:
                logger.exception("%s: Trying to reconnect", self.name)
                await asyncio.sleep(dly)
                dly = min(5*60, dly*1.5)
            else:
                logger.info("%s: Restarting done", self.name)
                return

    def restart(self, exc=None):
        logger.warn("%s: Restarting due to %s", self.name, exc)
        t = asyncio.ensure_future(self._restart())
        t.add_done_callback(self._restart_done)

    async def start_client(self)
	t,p = await self.loop.create_connection(partial(AioModbusClientProtocol, reconnect=self.restart), host=self.host, port=self.port)
	self.proto = p

    async def prepare1(self):
        await super().prepare1()
        self.end = asyncio.Event(loop=self.cmd.loop)
        self.stats = Stats()
        logger.debug("Start: %s",self.name)

        try:
            cfg = self.cfg
            self.host = cfg['host']
            if not self.host:
                raise KeyError(self.host)
        except KeyError:
            raise ConfigError("You need to specify a host")
        if self.host[0] == '/': # local device
            raise NotImplementedError("local modbus")

        else:
            if ':' in self.host:
                self.host,self.port=self.host.split(':')
            else:
                self.port = 502

            await self.start_client()

    async def run(self):
        await self.prepare1()
        await self.prepare2()

        await self.end.wait()

        logger.debug("Stop: %s",self.name)
        self.proto.stop()

    def stop(self):
        logger.debug("Stopping: %s",self.name)
        self.end.set()

    async def execute(self,request):
        async with self.stats:
            return (await self.proto.execute(request))

    def get_stats(self):
        return self.stats.state

Device.register("config","host", cls=str, doc="Host[:port] to connect to, or /dev/serial")


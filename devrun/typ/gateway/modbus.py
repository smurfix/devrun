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

# This code implements a Modbus gateway.
# Its main use is to multiplex multiple clients to one connection,
# in order to support dumb Modbus/TCP-enabled devices which cannot
# handle more than one connection.

import asyncio
import sys
from devrun.support.modbus import ModbusException
from pymodbus.client.async import ModbusClientProtocol
from pymodbus.pdu import ExceptionResponse
from pymodbus.datastore import ModbusServerContext

from devrun.device import BaseDevice
from devrun.support.timing import Stats
from functools import partial
from twisted.internet.defer import Deferred

import logging
logger = logging.getLogger(__name__)

import devrun.util.twist # for monkeypatching Deferred

from pymodbus.exceptions import NotImplementedException
from pymodbus.interfaces import IModbusSlaveContext
from pymodbus.datastore.remote import RemoteSlaveContext as RSC
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.server.async import ModbusServerFactory as MSF, ModbusTcpProtocol
from pymodbus.internal.ptwisted import InstallManagementConsole

class AsyncModbusTcpProtocol(ModbusTcpProtocol):
    def _send_later(self,message,reg):
        message.registers = reg
        super()._send(message)
        
    def _err(self,*a,**k):
        import pdb; pdb.set_trace()
        pass

    def _send(self,message):
        if isinstance(message.registers,Deferred):
            message.registers.addCallback(partial(self._send_later,message))
            message.registers.addErrback(self._err)
        else:
            super()._send(message)

class ModbusServerFactory(MSF):
    protocol = AsyncModbusTcpProtocol

def StartTcpServer(context, identity=None, address=None, console=False):
    ''' Helper method to start the Modbus Async TCP server
    This is a copy of pymodbus.server.async.StartTcpServer, without the
    brain-dead "reactor.run()" call at the end
    '''
    from twisted.internet import reactor

    address = address or ("", Defaults.Port)
    framer  = ModbusSocketFramer
    factory = ModbusServerFactory(context, framer, identity)
    if console: InstallManagementConsole({'factory': factory})

    _logger.info("Starting Modbus TCP Server on %s:%s" % address)
    reactor.listenTCP(address[1], factory, interface=address[0])

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)


#---------------------------------------------------------------------------#
# Context
#---------------------------------------------------------------------------#
class RemoteSlaveContext(RSC):
    '''
    A forwarding modbus slave
    '''

    def validate(self, fx, address, count=1):
        ''' Validation is disabled here '''
        return True

    def getValues(self, fx, address, count=1):
        ''' Get values from the remote server

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: A Deferred with the requested values from a:a+c
        '''
        logger.debug("get values[%d] %d:%d" % (fx, address, count))
        result = self.__get_callbacks[self.decode(fx)](address, count)
        result.addCallback(lambda r: self.__extract_result(self.decode(fx), r))
        return result

class TcpClient(ModbusClientProtocol):
    pass

class Device(BaseDevice):
    """ModBus gateway"""
    help = """\
This is a Modbus gateway.

It translates incoming requests to device N to go out to device X.
"""

    proto = None

    async def prepare1(self):
        from twisted.internet import reactor,protocol

        await super().prepare1()
        self.nr = self.cfg['devices']
        self.devices = {}
        for i in range(1,self.nr+1):

            cfg = self.loc['dev_%d' % i]
            host = cfg['host']
            if host[0] == '/': # local device
                raise NotImplementedError("local modbus")
            else:
                if ':' in host:
                    host,port=host.split(':')
                else:
                    port = 502
            client = protocol.ClientCreator(reactor, TcpClient).connectTCP(host,port)
            client = await client.asFuture(reactor._asyncioEventloop)

            ctx = RemoteSlaveContext(client)
            self.devices[i] = ctx

        self.server = ModbusServerContext(slaves=self.devices, single=False)
        StartTcpServer(self.server, address=("",self.cfg.get('port',502)))

    async def run(self):
        await self.prepare1()

        self.end = asyncio.Event(loop=self.cmd.loop)
        self.stats = Stats()
        logger.debug("Start: %s",self.name)

        await self.prepare2()

        await self.end.wait()

        logger.debug("Stop: %s",self.name)
        for c in self.devices.values():
            c.stop()
        self.server.stop()

    def stop(self):
        logger.debug("Stopping: %s",self.name)
        self.end.set()

    def get_stats(self):
        return self.stats.state

Device.register("config","host", cls=str, doc="Host[:port] to connect to, or /dev/serial")


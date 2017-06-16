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
        
    def _send(self,message):
        if isinstance(message.registers,Deferred):
            message.registers.addCallback(partial(self._send_later,message))
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

#    def __init__(self, client):
#        ''' Initializes the datastores
#
#        :param client: The client to retrieve values with
#        '''
#        self._client = client
#        self.__build_mapping()
#
#    def reset(self):
#        ''' Resets all the datastores to their default values '''
#        raise NotImplementedException()
#
    def validate(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        '''
        logger.debug("validate[%d] %d:%d" % (fx, address, count))
        return True
#
    def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        # TODO deal with deferreds
        #import pdb;pdb.set_trace()
        logger.debug("get values[%d] %d:%d" % (fx, address, count))
        result = self.__get_callbacks[self.decode(fx)](address, count)
        result.addCallback(lambda r: self.__extract_result(self.decode(fx), r))
        #result = await result
        return result

#    def setValues(self, fx, address, values):
#        ''' Sets the datastore with the supplied values
#
#        :param fx: The function we are working with
#        :param address: The starting address
#        :param values: The new values to be set
#        '''
#        # TODO deal with deferreds
#        logger.debug("set values[%d] %d:%d" % (fx, address, len(values)))
#        return self.__set_callbacks[self.decode(fx)](address, values)
#
#    def __str__(self):
#        ''' Returns a string representation of the context
#
#        :returns: A string representation of the context
#        '''
#        return "Remote Slave Context(%s)" % self._client
#
#    def __build_mapping(self):
#        '''
#        A quick helper method to build the function
#        code mapper.
#        '''
#        self.__get_callbacks = {
#            'd': lambda a, c: self._client.read_discrete_inputs(a, c),
#            'c': lambda a, c: self._client.read_coils(a, c),
#            'h': lambda a, c: self._client.read_holding_registers(a, c),
#            'i': lambda a, c: self._client.read_input_registers(a, c),
#        }
#        self.__set_callbacks = {
#            'd': lambda a, v: self._client.write_coils(a, v),
#            'c': lambda a, v: self._client.write_coils(a, v),
#            'h': lambda a, v: self._client.write_registers(a, v),
#            'i': lambda a, v: self._client.write_registers(a, v),
#        }
#
#    def __extract_result(self, fx, result):
#        ''' A helper method to extract the values out of
#        a response.  TODO make this consistent (values?)
#        '''
#        if result.function_code < 0x80:
#            if fx in ['d', 'c']: return result.bits
#            if fx in ['h', 'i']: return result.registers
#        else: return result

class TcpClient(ModbusClientProtocol):
    def execute(self,request):
        #import pdb;pdb.set_trace()
        return super().execute(request)

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


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
from devrun.support.modbus import AioModbusClientProtocol
from pymodbus.pdu import ExceptionResponse, ModbusExceptions
from pymodbus.datastore import ModbusServerContext
from pymodbus.factory import ServerDecoder
from pymodbus.compat import byte2int, int2byte
from pymodbus.exceptions import NoSuchSlaveException

from devrun.device import BaseDevice
from devrun.support.timing import Stats
from functools import partial
from inspect import isawaitable
from binascii import b2a_hex

import logging
logger = logging.getLogger(__name__)

from pymodbus.exceptions import NotImplementedException
from pymodbus.interfaces import IModbusSlaveContext
from pymodbus.datastore.remote import RemoteSlaveContext as RSC
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.server.async import ModbusServerFactory as MSF, ModbusTcpProtocol
from pymodbus.constants import Defaults
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusAccessControl

class AioModbusServerProtocol:
    ''' Implements a modbus server in twisted '''

    task = None
    def __init__(self, framer=ModbusSocketFramer, decoder=ServerDecoder,
            store=None, control=None,access=None, ignore_missing_slaves=None, loop=None, timeout=1):
        self.decoder = decoder()
        self.framer = framer(self.decoder)
        self.store = store or ModbusServerContext()
        self.control = control or ModbusControlBlock()
        self.access = access or ModbusAccessControl()
        self.ignore_missing_slaves = ignore_missing_slaves if ignore_missing_slaves is not None \
            else Defaults.IgnoreMissingSlaves
        self.loop = loop
        self.q = asyncio.Queue(loop=loop)
        self.timeout = timeout

    def connection_made(self, transport):
        ''' Callback for when a client connects
        '''
        logger.debug("Client Connected")
        self.transport = transport
        if self.task is None:
            self.task = asyncio.ensure_future(self.exec_task(), loop=self.loop)

    def eof_received(self, *foo):
        logger.debug("Client EOF: %s", foo)
        self.connection_lost(None)

    def connection_lost(self, exc):
        ''' Callback for when a client disconnects

        :param exc: The client's reason for disconnecting
        '''
        logger.debug("Client Disconnected: %s", exc)
        self.transport = None
        if self.task is not None:
            self.task.cancel()
            self.task = None

    def data_received(self, data):
        ''' Callback when we receive any data

        :param data: The data sent by the client
        '''
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(' '.join([hex(byte2int(x)) for x in data]))
        if not self.control.ListenOnly:
            self.framer.processIncomingPacket(data, self._execute)

    def _execute(self, request):
        ''' Executes the request and returns the result

        :param request: The decoded request message
        '''
        self.q.put_nowait(request)

    async def exec_task(self):
        while True:
            request = await self.q.get()
            try:
                await self._execute2(request)
            except Exception as ex:
                logger.exception("GW")
                raise

    async def _execute2(self, request):
        try:
            context = self.store[request.unit_id]
            response = request.execute(context)
            if isawaitable(response.registers):
                response.registers = await asyncio.wait_for(response.registers, self.timeout)
        except NoSuchSlaveException as ex:
            logger.debug("requested slave does not exist: %s", request.unit_id)
            if self.ignore_missing_slaves:
                return # the client will simply timeout waiting for a response
            response = request.doException(ModbusExceptions.GatewayNoResponse)
        except asyncio.TimeoutError:
            response = request.doException(ModbusExceptions.GatewayNoResponse)
        except Exception as ex:
            logger.debug("Datastore unable to fulfill request: %s", ex)
            response = request.doException(ModbusExceptions.SlaveFailure)
        #self.framer.populateResult(response)
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self._send(response)

    def _send(self, message):
        ''' Send a request (string) to the network

        :param message: The unencoded modbus response
        '''
        if message.should_respond:
            self.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('send: %s', b2a_hex(pdu))
            return self.transport.write(pdu)

#---------------------------------------------------------------------------#
# Context
#---------------------------------------------------------------------------#
class RemoteSlaveContext(RSC):
    '''
    A forwarding modbus slave

    This has the same name as the superclass so that overriding __foo works
    '''

    def validate(self, fx, address, count=1):
        ''' Validation is disabled here '''
        return True

    async def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        # TODO deal with deferreds
        logger.debug("get values[%d:%d] %d:%d", fx, self.unit, address, count)
        result = await self.__get_callbacks[self.decode(fx)](address, count, unit=self.unit)
        if isawaitable(result):
            result = await result
        return self.__extract_result(self.decode(fx), result)

    def __build_mapping(self):
        '''
        A quick helper method to build the function
        code mapper.
        '''
        self.__get_callbacks = {
            'd': self._client.read_discrete_inputs,
            'c': self._client.read_coils,
            'h': self._client.read_holding_registers,
            'i': self._client.read_input_registers,
        }
        self.__set_callbacks = {
            'd': self._client.write_coils,
            'c': self._client.write_coils,
            'h': self._client.write_registers,
            'i': self._client.write_registers,
        }

class Device(BaseDevice):
    """ModBus gateway"""
    help = """\
This is a Modbus gateway.

It translates incoming requests to device N to go out to device X.
"""

    proto = None

    async def prepare1(self):
        await super().prepare1()
        self.nr = self.cfg['devices']
        self.devices = {}
        clients = {}
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
            try:
                client = clients[(host,port)]
            except KeyError:
                (t,p) = await self.loop.create_connection(AioModbusClientProtocol, host=host, port=port)
                client = clients[(host,port)] = p

            ctx = RemoteSlaveContext(client)
            ctx.unit = cfg.get('unit',1)
            self.devices[i] = ctx

        self.ctx = ModbusServerContext(slaves=self.devices, single=False)
        self.server = await self.loop.create_server(lambda: AioModbusServerProtocol(store=self.ctx, loop=self.loop, timeout=self.cfg.get('timeout',3)), host=None, port=self.cfg.get('port',502))

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


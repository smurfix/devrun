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

# modbus asyncio adapter

import asyncio

from pymodbus.client.common import ModbusClientMixin
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer, FifoTransactionManager, DictTransactionManager
from pymodbus.factory import ClientDecoder, ExceptionResponse

import logging
logger = logging.getLogger(__name__)

class ModbusException(RuntimeError):
    def __init__(self,err):
        self.code = err.exception_code
    def __repr__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.code)
    def __str__(self):
        return '%s:%s' % (self.__class__.__name__, self.code)

class AioModbusClientProtocol(ModbusClientMixin):
    transport = None

    def __init__(self, framer=None, loop=None, **kwargs):
        ''' Initializes the framer module

        :param framer: The framer to use for the protocol
        '''
        self.loop = loop
        self.framer = framer or ModbusSocketFramer(ClientDecoder())
        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self, **kwargs)
        else:
            self.transaction = FifoTransactionManager(self, **kwargs)

    def connection_made(self, transport):
        self.transport = transport
    
    def connection_lost(self, exc=None):
        self.transport = None
        if exc is None:
            exc = EOFError
        for tid in self.transaction:
            self.transaction.getTransaction(tid).set_exception(exc)
    
    def data_received(self, data):
        self.framer.processIncomingPacket(data, self._handleResponse)

    def eof_received(self):
        logger.info("Lost connection: %s",self)

    def _buildResponse(self, tid):
        ''' Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        '''
        if self.transport is None:
            raise ConnectionException('Client is not connected')

        d = asyncio.Future(loop=self.loop)
        self.transaction.addTransaction(d, tid)
        return d

    def _handleResponse(self, reply):
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.getTransaction(tid)
            if handler:
                try:
                    if isinstance(reply, ExceptionResponse):
                        handler.set_exception(ModbusException(reply))
                    else:
                        handler.set_result(reply)
                except asyncio.CancelledError:
                    pass
            else:
                logger.debug("Unrequested message: %s", reply)

    async def execute(self, request):
        request.transaction_id = self.transaction.getNextTID()
        d = self._buildResponse(request.transaction_id)
        self.transport.write(self.framer.buildPacket(request))
        return (await d)


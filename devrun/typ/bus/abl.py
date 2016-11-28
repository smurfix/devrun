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
from devrun.support.abl import ReqReply,Request,Reply,RT

import logging
logger = logging.getLogger(__name__)

class NoData(RuntimeError):
    pass

class EvcProtocol(asyncio.Protocol):
    buf = b''

    def __init__(self, parent):
        self.parent = parent

    def connection_made(self, transport):
        self.transport = transport
        self.parent.protocol = self

    def data_received(self, data):
        logger.debug("raw recv: %s",repr(data))
        self.buf += data
        while True:
            i = self.buf.find(b'\n')
            if i < 0:
                break
            data,self.buf = self.buf[0:i],self.buf[i+1:]
            if data:
                data = ReqReply.build(data)
                logger.debug("recv: %s",data)
                self.parent.msg_received(data)

    def send(self,req):
        logger.debug("send: %s",str(req))
        self.transport.write(req.bytes)

    def connection_lost(self, exc):
        self.parent.stop()

class Device(BaseDevice):
    """ABL link"""
    help = """\
This is a link to EV charge controllers by ABL Sursum.
They have a half-duplex RS485 interface.

You can connect to a local serial interface,
or to a remote interface by way of a "socat" command or similar:

    socat TCP-LISTEN:50422,reuseaddr,keepalive=30 /dev/rs422,b38400,raw,echo=0,crtscts=0,clocal=1

Be sure to auto-restart this command,
as it exits when the client terminates.
"""

    proto = None

    async def run(self):
        logger.info("Start: %s",self.name)
        self.q = asyncio.Queue()
        self.connected = asyncio.Event(loop=self.cmd.loop)

        try:
            cfg = self.loc.get('config',{})
            host = cfg['host']
            if not host:
                raise KeyError(host)
        except KeyError:
            raise ConfigError("You need to specify a host")
        if host[0] == '/': # local device
            from serial_asyncio import create_serial_connection

            await create_serial_connection(self.cmd.loop, lambda:EvcProtocol(self), host, baudrate=38400)
        else:
            if ':' in host:
                host,port=host.split(':')
            else:
                port = 50485

            await self.cmd.loop.create_connection(lambda:EvcProtocol(self), host,port)

        await self.connected.wait()
        # ensure that line noise doesn't block anything
        await asyncio.sleep(0.5)
        self.proto.transport.write(b'XXX\r\n')
        await asyncio.sleep(0.5)
        logger.info("Running: %s",self.name)
        self.cmd.reg.bus[self.name] = self

        while self.connected.is_set():
            d,f = await self.q.get()
            if d is None:
                break
            self.req = asyncio.Future(loop=self.cmd.loop)
            self.req_msg = d
            self.proto.send(d)
            try:
                res = await asyncio.wait_for(self.req, 0.5, loop=self.cmd.loop)
            except Exception as exc:
                f.set_exception(exc)
            except BaseException as exc:
                f.set_exception(exc)
                raise
            else:
                f.set_result(res)
            finally:
                self.req = None
                self.req_msg = None

        logger.info("Stop: %s",self.name)
        self.proto.transport.close()

    def start(self,proto):
        self.proto = proto
        self.connected.set()

    def stop(self):
        logger.info("Stopping: %s",self.name)
        self.q.put((None,None))

    def msg_received(self,d):
        r,self.req_msg = self.req_msg,None
        if r is None:
            logger.info("Unsolicited: %s",d)
        else:
            if r.nr == d.nr and r.a == d.a:
                self.req.set_result(d)
                if mon:
                    mon.write(d)
            else:
                self.req.set_exception(NoData(r.nr))
            return

        self.processor.main.write(d)
        if mon:
            mon.write(d)

    async def do_request(self,d):
        assert isinstance(d,Request)
        f = asyncio.Future(loop=self.cmd.loop)
        await self.q.put((d,f))
        try:
            res = await f
        except TimeoutError:
            res = None
        return res

    async def query(adr,func,b=None):
        req = Request(adr,func,b)
        res = await self.do_request(req)
        try:
            return int(res.b)
        except TypeError:
            return res.b

Device.register("config","host", cls=str, doc="Host[:port] to connect to, or /dev/serial")


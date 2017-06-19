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
from devrun.support.timing import Stats

from . import BaseDevice
from devrun.support.abl import ReqReply,Request,Reply,RT

import logging
logger = logging.getLogger(__name__)

class NoData(RuntimeError):
    pass

class EvcProtocol(asyncio.Protocol):
    buf = b''
    timer = None

    def __init__(self, parent):
        self.parent = parent

    def _flush(self):
        self.buf = b''
        self.timer = None

    def connection_made(self, transport):
        self.transport = transport
        self.parent.start(self)

    def data_received(self, data):
        # logger.info("raw recv: %s",repr(data))
        self.buf += data
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        while True:
            i = self.buf.find(b'\n')
            if i < 0:
                break
            data,self.buf = self.buf[0:i],self.buf[i+1:]
            if data:
                data = ReqReply.build(data)
                if data:
                    logger.debug("recv: %s",data)
                    self.parent.msg_received(data)
        if self.buf:
            self.timer = self.parent.cmd.loop.call_later(0.5,self._flush)

    def send(self,req):
        # logger.info("send: %s",str(req))
        if not isinstance(req,bytes):
            req = req.bytes
        self.transport.write(req)

    def connection_lost(self, exc):
        self.parent.restart()

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

    async def prepare1(self):
        await super().prepare1()
        self.q = asyncio.Queue()
        self.connected = asyncio.Event(loop=self.cmd.loop)
        self.stats = Stats()

    async def connect(self):
        try:
            host = self.cfg['host']
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
                port = 20422

            await self.cmd.loop.create_connection(lambda:EvcProtocol(self), host,port)

        await self.connected.wait()
        # ensure that line noise doesn't block anything
        await asyncio.sleep(0.3, loop=self.cmd.loop)
        self.proto.transport.write(b'XXX\r\n')
        await asyncio.sleep(0.7, loop=self.cmd.loop)

    async def run(self):
        await self.prepare1()
        await self.connect()
        await self.prepare2()

        while True:
            d,f = await self.q.get()
            if d is None:
                if f is None:
                    break
                await asyncio.sleep(0.5, loop=self.cmd.loop)

            self.req = asyncio.Future(loop=self.cmd.loop)
            self.req_msg = d
            async with self.stats:
                retries = 0
                while not f.done():
                    if self.req.done():
                        self.req = asyncio.Future(loop=self.cmd.loop)
                    if not self.connected.is_set():
                        await self.connect()
                    if retries:
                        logger.info("%s: Re-Sending %d %s", self.name,retries, repr(d))
                    self.proto.send(d)
                    try:
                        res = await asyncio.wait_for(self.req, 1.5, loop=self.cmd.loop)
                    except (asyncio.TimeoutError,NoData) as exc:
                        logger.info("%s: Timeout on %s", self.name,repr(d))
                        retries += 1
                        if retries > 5:
                            f.set_exception(exc)
                            break
                        self.req_msg = None
                        self.proto.send(b'XXX\r\n')
                        await asyncio.sleep(0.7, loop=self.cmd.loop)
                        self.req_msg = d
                    except Exception as exc:
                        f.set_exception(exc)
                    except BaseException as exc:
                        f.set_exception(exc)
                        raise
                    else:
                        f.set_result(res)
                self.req = None
                self.req_msg = None

        logger.info("Stop: %s",self.name)
        self.proto.transport.close()

    def get_stats(self):
        return self.stats.state

    def start(self,proto):
        self.proto = proto
        self.connected.set()

    def stop(self):
        logger.info("Stopping: %s",self.name)
        self.q.put((None,None))

    def restart(self):
        logger.info("Restarting: %s",self.name)
        # self.q.put((None,True))

    def msg_received(self,d):
        r,self.req_msg = self.req_msg,None
        if r is None:
            logger.info("Unsolicited: %s",d)
        else:
            if r.nr == d.nr and r.a == d.a:
                self.req.set_result(d)
            else:
                pass ## XXX timeout will catch this?
                #self.req.set_exception(NoData(r.nr))

    async def do_request(self,d):
        assert isinstance(d,Request)
        f = asyncio.Future(loop=self.cmd.loop)
        await self.q.put((d,f))
        try:
            res = await f
        except TimeoutError:
            res = None
        return res

    async def query(self,adr,func,b=None):
        req = Request(adr,func,b)
        while True:
            res = await self.do_request(req)
            if res is None:
                await asyncio.sleep(0.2,loop=self.cmd.loop)
                continue
            try:
                return int(res.b)
            except TypeError:
                return res.b

Device.register("config","host", cls=str, doc="Host[:port] to connect to, or /dev/serial")


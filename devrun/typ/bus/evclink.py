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

class NoData(RuntimeError):
    pass

class ReqReply:
    """encapsulate a request/reply exchanged while talking to the evc"""
    lead = None
    def __init__(self, nr,a,b=None, *, callback=None):
        self.nr = nr
        self.a = a
        self.b = b

    def __str__(self):
        return self.bytes().decode('ascii').strip()

    @property
    def bytes(self):
        r = "%c%d %02d" % (self.lead,self.nr,self.a)
        if self.b is not None:
            r += ' ' + self.b
        r += '\r\n'
        return r.encode('ascii')

    @staticmethod
    def build(s,callback=None):
        s = s.decode('ascii')
        if s[0] == Request.lead:
            c = Request
        elif s[0] == Reply.lead:
            c = Reply
        else:
            raise RuntimeError('Unknown input: '+repr(s))
        s = s[1:].strip('\n').strip('\r').strip(' ').split(' ')
        s[0] = int(s[0])
        s[1] = int(s[1])

        return c(*s)

class Request(ReqReply):
    "Encapsulates a request"
    lead = '!'
class Reply(ReqReply):
    "Encapsulates a reply"
    lead = '>'


class EvcProtocol(asyncio.Protocol):
    buf = ''

    def __init__(self, parent):
        self.parent = parent

    def connection_made(self, transport):
        self.transport = transport
        self.parent.protocol = self

    def data_received(self, data):
        self.buf += data
        while True:
            i = self.buf.index(b'\n')
            if i < 0:
                break
            data,self.buf = self.buf[0:i],self.buf[i:]
            self.parent.msg_received(ReqReply(data))
        if b'\n' in data:
            self.transport.close()

    def send(self,req):
        self.transport.write(req.bytes)
        
    def connection_lost(self, exc):
        self.parent.stop()

class Device(BaseDevice):
    """EVC link"""
    help = """\
This is a link to EV chargers by ABL Sursum.
They have a half-duplex RS485 interface.

You can connect to a local serial interface,
or to a remote interface by way of a "socat" command or similar:

    socat TCP-LISTEN:50422,reuseaddr,keepalive=30 /dev/rs422,b38400,raw,echo=0,crtscts=0,clocal=1

Be sure to auto-restart this command,
as it exits when the client terminates.
"""
    
    proto = None

    async def run(self):
        self.q = asyncio.Queue()

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

        assert self.proto is not None
        # ensure that line noise doesn't block anything
        await asyncio.sleep(0.5)
        self.proto.transport.write(b'XXX\r\n')
        await asyncio.sleep(0.5)

        while True:
            d,f = await self.q.get()
            if d is None:
                break
            self.req = Future()
            self.req_msg = d
            super().write(d.bytes())
            try:
                res = await wait_for(self.req, 0.5)
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
        self.proto.transport.close()

    def stop(self):
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
        f = Future()
        await self.q.put((d,f))
        try:
            res = await f
        except TimeoutError:
            res = None
        return res


Device.register("config","host", cls=str, doc="Host[:port] to connect to, or /dev/serial")


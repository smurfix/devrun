#!/usr/bin/env python
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
import inspect

from devrun.util import objects, import_string

import logging
logger = logging.getLogger(__name__)

class BaseDevice(object):
    INTERVAL = 5

    _reg = {}

    def __init__(self, name,cmd,loc):
        self.name = name
        self.cmd = cmd
        self.loc = loc

    def __repr__(self):
        try:
            return "‹%s:%s›" % (self.__class__.__module__.replace("devrun.",""),self.name)
        except AttributeError:
            return "‹%s:?›" % (self.__class__.__module__,)

    async def prepare1(self):
        """Override me. Call me first!"""
        self.cfg = self.loc.get('config',{})
        logger.debug("%s: starting", self.name)
        self._trigger = asyncio.Event(loop=self.cmd.loop)
        wait = self.cfg.get('wait-for',None)
        if wait is not None:
            a,b = wait.split('/')
            await getattr(self.cmd.reg,a).get(b)

    def trigger(self):
        """Run the next iteration of this device's loop now."""
        self._trigger.set()

    async def prepare2(self):
        """Override me. Call me last!"""
        getattr(self.cmd.reg,self.__module__.rsplit('.',2)[1])[self.name] = self
        logger.debug("%s: running", self.name)

    async def step1(self):
        """Override me. Call me first!"""
        pass

    async def step2(self):
        """Override me. Call me last!"""
        await self.cmd.amqp.alert("update."+self.__module__.rsplit('.',2)[1], _data=self.get_state())

    @property
    def interval(self):
        return self.cfg.get('interval',self.INTERVAL)

    async def run(self):

        await self.prepare1()
        await self.prepare2()

        while True:
            await self.step1()
            await self.step2()

            try:
                await asyncio.wait_for(self._trigger.wait(), self.interval, loop=self.cmd.loop)
            except asyncio.TimeoutError:
                pass
            else:
                self._trigger.clear()

    @classmethod
    def register(_cls,*path,cls=None,doc=None):
        r = _cls._reg
        for p in path:
            assert p
            assert '' not in r
            if p not in r:
                r[p] = {}
            r = r[p]
        r[''] = cls
        r['doc'] = doc

    @classmethod
    def registrations(cls):
        """Lists path,type,docstr of variables"""
        r = cls._reg
        def get(p,r):
            for a,b in r.items():
                cls = b.get('',None)
                if cls is None:
                    yield from get(p+(a,),b)
                else:
                    yield p+(a,),cls,b['doc']
        return get((),r)

    @property
    def schema(self):
        return list(('.'.join(a),b.__name__,c) for a,b,c in self.registrations())

    def get_state(self):
        res = {'name':self.name, 'type':self.__module__.rsplit('.',1)[1]}
        doc = self.loc.get('doc',None)
        if doc is not None:
            res['doc'] = doc
        return res

BaseDevice.register("config","interval", cls=float, doc="delay between measurements")

class NotYetError(RuntimeError):
    pass

###########################################################################

class Registry:
    """
        Store links to devices which may not exist yet.

        Usage:
            Register:
                reg.type[name] = dev
                # BaseDevice.step2() does that for you

            Retrieve:
                dev = await reg.type.get(name)

            Trigger timeouts:
                reg.done()

        """
    def __init__(self, loop):
        self.reg = {}
        self.loop = loop

    def __getattr__(self,k):
        if k.startswith('_'):
            return super().__getattr__(k)
        try:
            return self.reg[k]
        except KeyError:
            res = self.reg[k] = _SubReg(k,self.loop)
            return res

    def __iter__(self):
        for v in self.reg.values():
            yield from v

    @property
    def types(self):
        """Known types.
            Yields tuples of name,num_devices,class.
            """
        for k,v in self.reg.items():
            yield k,len(v),import_string('devrun.typ.%s.Type' % (k,))
        
    def done(self):
        """Triggers a timeout error on all outstanding futures.
            Returns the number of aborts."""
        t = None
        n = 0
        for f in self:
            if isinstance(f,asyncio.Future):
                if t is None:
                    t = asyncio.TimeoutError()
                f.set_exception(t)
                n += 1
        return n

class _SubReg:
    def __init__(self,name,loop):
        self.name = name
        self.loop = loop
        self.reg = {}

    def __getitem__(self,k):
        dev = self.reg[k]
        if isinstance(dev,asyncio.Future):
            raise NotYetError(self.name,k)
        return dev

    def items(self):
        return self.reg.items()
    def keys(self):
        return self.reg.keys()
    def __len__(self):
        return len(self.reg)

    def __iter__(self):
        for v in self.reg.values():
            yield v

    def __setitem__(self,k,v):
        logger.debug("reg %s.%s",self.name,k)
        f = self.reg.get(k,None)
        if f is None:
            pass
        elif isinstance(f,asyncio.Future):
            if not f.done():
                f.set_result(v)
        else:
            raise RuntimeError('already known',self.name,k,f)
        self.reg[k]=v

    async def get(self,k, create=True):
        f = self.reg.get(k,None)
        if f is None:
            if not create:
                raise KeyError(k)
            logger.debug("wait for %s.%s",self.name,k)
            f = self.reg[k] = asyncio.Future(loop=self.loop)
        elif isinstance(f,asyncio.Future):
            logger.debug("also wait for %s.%s",self.name,k)
            pass
        else:
            logger.debug("found %s.%s",self.name,k)
            return f
        return (await f)


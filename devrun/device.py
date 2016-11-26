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

class BaseDevice(object):
    _reg = {}

    def __init__(self, name,cmd,loc):
        self.name = name
        self.cmd = cmd
        self.loc = loc

    async def run(self):
        pass

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

class NotYetError(RuntimeError):
    pass

class Registry:
    """
        Store links to devices which may not exist yet.

        Usage:
            Register:
                reg.type[name] = dev

            Retrieve:
                dev = await reg.type.get(name)

            Trigger timeouts:
                reg.done()
        
        """
    def __init__(self):
        self.reg = {}

    def __getattr__(self,k):
        if k.startswith('_'):
            return super().__getattr__(k)
        try:
            return self.reg[k]
        except KeyError:
            res = self.reg[k] = _SubReg(k)
            return res

    def __iter__(self):
        for v in self.reg.values():
            yield from v

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
    def __init__(self,name):
        self.name = name
        self.reg = {}

    def __getitem__(self,k):
        dev = self.reg[k]
        if isinstance(dev,asyncio.Future):
            return NotYetError(self.name,k)

    def __iter__(self):
        for v in self.reg.values():
            yield v

    def __setitem__(self,k,v):
        f = self.reg.get(k,None)
        if f is None:
            pass
        elif isinstance(f,asyncio.Future):
            f.set_result(v)
        else:
            raise RuntimeError('already known',self.name,k,f)
        self.reg[k]=v

    async def get(self,k):
        f = self.reg.get(k,None)
        if f is None:
            f = self.reg[k] = asyncio.Future()
        elif isinstance(f,asyncio.Future):
            pass
        else:
            return f
        return (await f)


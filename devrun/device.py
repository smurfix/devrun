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

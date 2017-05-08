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

from pprint import pprint

from . import BaseCommand

class Command(BaseCommand):
    "Send an 'info' RPC message, print the result"
    help = """\
info ‹subsystem› ‹devicename› cmd|get ‹command›
    -- Send an 'info' RPC message and print the result.

info
       list of active subsystems
info ‹subsystem›
       With one argument, lists that subsystem's active devices.
info ‹subsystem› ‹devicename›
       return that device's config and a list of commands it understands.
info ‹subsystem› ‹devicename› cmd|get
       lists commands of that type in greater detail
info ‹subsystem› ‹devicename› cmd|get ‹command›
       display that command's arguments
"""

    async def run(self, *args):
        """Basic 'info' rpc call"""
        if self.amqp is None:
            raise RuntimeError("You did not configure an AMQP connection")
        a=[]
        kv={}
        for arg in args:
            try:
                k,v = arg.split('=',1)
            except ValueError:
                a.append(arg)
            else:
                try:
                    v=int(v)
                except ValueError:
                    try:
                        v=float(v)
                    except ValueError:
                        if len(v)>1 and v[0]==v[-1] and v[0] in '\'"':
                            v=v[1:-1]
                        pass
                kv[k]=v
        if len(a) > 0:
            kv['_subsys'] = a[0]
            if len(a) > 1:
                kv['_dev'] = a[1]
                if len(a) > 2:
                    kv['_cmd'] = a[2]
                    if len(a) > 3:
                        kv['_proc'] = a[3]
                        if len(a) > 4:
                            raise NotImplementedError('max four arguments')
        res = await self.amqp.rpc('info',**kv)
        pprint(res)


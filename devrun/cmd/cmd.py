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
    "Send a 'cmd' RPC message, print the result"
    help = """\
cmd
    -- Send a 'cmd' RPC message and print the result.

       Arguments: at least ‹subsystem› ‹devicename› ‹command›
       Other arguments depend on the command:
       display them with 'info ‹subsystem› ‹devicename› cmd ‹command›'.
"""

    async def run(self, *args):
        """Basic 'cmd' rpc call"""
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
        if len(a) < 3:
            raise NotImplementedError('need at least three arguments')
        kv['_subsys'] = a[0]
        kv['_dev'] = a[1]
        kv['_cmd'] = a[2]
        if len(a) > 3:
            kv['_a'] = a[3:]
        res = await self.amqp.rpc('cmd',**kv)
        pprint(res)


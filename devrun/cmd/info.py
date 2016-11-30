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

import sys
import asyncio
from traceback import print_exc
from collections.abc import Mapping
from qbroker.unit import CC_DICT
from pprint import pprint

from . import BaseCommand
from devrun.util import objects, import_string
from devrun.typ import BaseType
from devrun.etcd.types import EvcDevice

class Command(BaseCommand):
    "Send an 'info' RPC message, print the result"
    help = """\
info
    -- Send an 'info' RPC message and print the result.

       Without arguments, lists active subsystems.
       With one argument, lists that subsystem's active devices.
       With two arguments, lists that device's current state.
"""

    async def run(self, *args):
        """Basic 'info' rpc call"""
        if self.amqp is None:
            raise RuntimeError("You did not configure an AMQP connection")
        a=[]
        k={}
        for arg in args:
            try:
                k,v = arg.split('=',1)
            except ValueError:
                a.append(arg)
        if len(a) > 0:
            k['_subsys'] = a[0]
            if len(a) > 1:
                k['_dev'] = a[1]
                if len(a) > 2:
                    raise NotImplementedError('max two arguments')
        res = await self.amqp.rpc('info',**k)
        pprint(res)


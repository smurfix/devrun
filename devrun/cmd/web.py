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
import inspect
from traceback import print_exc
from collections.abc import Mapping

from . import BaseCommand
from devrun.web import App

class Command(BaseCommand):
    "Run a web server"
    help = """\
web
    -- run a web server. Usage: web [[bind-to] port]
                           Defaults:    any    9980
"""

    app = None
    bindto = '0.0.0.0'
    port = 9980

    async def run(self, *args):
        self.loop = self.opt.loop
        if len(args) > 2:
            print("Usage: run", file=sys.stderr)
            return 1
        if args:
            self.port = atoi(args[-1])
            if len(args) > 1:
                self.bindto = args[0]
        self.app = App(self)
        await self.app.start(self.bindto,self.port)

        while True:
            await asyncio.sleep(9999,loop=self.loop)

    async def stop(self):
        if self.app is not None:
            await self.app.stop()
        await super().stop()


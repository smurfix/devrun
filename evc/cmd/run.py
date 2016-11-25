# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This file is part of evc, a comprehensive controller and monitor for
## chargers of electric vehicles.
##
## evc is Copyright © 2016 by Matthias Urlichs <matthias@urlichs.de>,
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

from . import BaseCommand
from evc.util import objects, import_string
from evc.typ import BaseType
from evc.etcd.types import EvcDevice

class Command(BaseCommand):
    "Run the whole system"
    help = """\
run
    -- process everything
"""

    async def run(self, *args):
        if args:
            print("Usage: run", file=sys.stderr)
            return 1
        self.cls = {}
        self.loop = asyncio.get_event_loop()
        self.endit = asyncio.Event()
        def ended(f):
            try:
                exc = f.exception()
            except asyncio.CancelledError:
                exc = None
            except Exception as e:
                exc = e
            except BaseException:
                exc = None
            finally:
                if exc is not None:
                    print_exc(exc)
                self.endit.set()

        evc = self.cfg['evc']
        for cls,devs in evc.items():
            if not isinstance(devs,Mapping):
                continue
            g = self.cls[cls] = {}
            for name,dev in devs.items():
                if self.endit.is_set():
                    break
                if not isinstance(dev,Mapping):
                    continue
                d = import_string('evc.typ.%s.%s.Device' % (cls,dev['type']))
                d = d(name,self,dev)
                j = asyncio.ensure_future(d.run())
                j.add_done_callback(ended)
                gg = g[name] = (d,j)

        await self.endit.wait()

    async def stop(self):
        for cls in self.cls.values():
            for c,j in cls.values():
                try:
                    j.cancel()
                except Exception:
                    continue
                try:
                    await j
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print_exception(e.__class__,e,e.__traceback__)


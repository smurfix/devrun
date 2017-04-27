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
from qbroker.unit import CC_DICT

from . import BaseCommand, CMD_TYPES
from devrun.util import objects, import_string
from devrun.typ import BaseType
from devrun.etcd.types import EvcDevice

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
        self.endit = asyncio.Event(loop=self.loop)
        def ended(f):
            try:
                f.result()
            except asyncio.CancelledError:
                pass
            except KeyboardInterrupt:
                self.endit.set()
            except BaseException:
                print_exc()

        for cls,devs in self.cfg['devices'].items():
            if not isinstance(devs,Mapping):
                continue
            g = self.cls[cls] = {}
            for name,dev in devs.items():
                if self.endit.is_set():
                    break
                if not isinstance(dev,Mapping):
                    continue
                d = import_string('devrun.typ.%s.%s.Device' % (cls,dev['type']))
                d = d(name,self,dev)
                j = asyncio.ensure_future(d.run())
                j.add_done_callback(ended)
                gg = g[name] = (d,j)

        await self.endit.wait()

    async def start(self):
        await super().start()
        if self.amqp is None:
            return
        for k in dir(self):
            if k.startswith('rpc_'):
                await self.amqp.register_rpc_async(k[4:],getattr(self,k), call_conv=CC_DICT)

    async def rpc_cmd(self, _subsys, _dev, _cmd, _a=(),**kw):
        v = await getattr(self.reg,_subsys).get(_dev, create=False)
        v = getattr(v,'cmd_'+_cmd)
        res = v(*_a,**kw)
        if inspect.isawaitable(res):
            res = await res
        return res

    async def rpc_get(self, _subsys, _dev, _cmd, _a=(),**kw):
        v = await getattr(self.reg,_subsys).get(_dev, create=False)
        v = getattr(v,'get_'+_cmd)
        res = v(*_a,**kw)
        if inspect.isawaitable(res):
            res = await res
        return res

    async def rpc_info(self, _subsys=None, _dev=None, _cmd=None, _proc=None, **ak):
        if _subsys is None:
            assert _dev is None
            res = {}
            for k,n,t in self.reg.types:
                res[k] = {'n':n,'doc':t.__doc__,'help':t.help}
        elif _dev is None:
            res = {}
            for k,v in getattr(self.reg,_subsys).items():
                if isinstance(v,asyncio.Future):
                    if not v.done():
                        res[k] = {'type':'Future','state':repr(v)}
                        continue
                    else:
                        v = v.result()
                res[k] = v.get_state()
        else:
            v = await getattr(self.reg,_subsys).get(_dev, create=False)
            if _cmd is None:
                res = {
                    'data': v.loc,
                    'schema': v.schema,
                   }
                for _cmd in CMD_TYPES:
                    a = []
                    _cmd += '_'
                    for k in dir(v):
                        if k.startswith(_cmd):
                            a.append(k[len(_cmd):])
                    if a:
                        res[_cmd[:-1]] = a
            elif _cmd not in CMD_TYPES:
                raise NotImplementedError(_cmd)
            elif _proc is None:
                res = {}
                _cmd += '_'
                for k in dir(v):
                    if k.startswith(_cmd):
                        res[k[len(_cmd):]] = getattr(v,k).__doc__
            else:
                v = getattr(v,_cmd+'_'+_proc)
                args, varargs, varkw, defaults = inspect.getargspec(v)
                args = args[1:]
                varargs = bool(varargs)
                varkw = bool(varkw)
                res = {'doc':v.__doc__, 'args':args, 'varargs':varargs, 'varkw':varkw, 'defaults':defaults}
        return res

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
                    print_exc()


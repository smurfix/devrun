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

# common parser

import argparse
import os
from collections.abc import Mapping
import qbroker
import asyncio

from devrun.util import import_string, load_cfg
from devrun.device import Registry

CMD_TYPES={'get','cmd'}

def parser(**kw):
    if 'formatter_class' not in kw:
        kw['formatter_class'] = argparse.RawDescriptionHelpFormatter
    res = argparse.ArgumentParser(**kw)
    res.add_argument('-c', '--config', dest='config', default=os.environ.get('DEVRUN_CONFIG','/etc/devrun.cfg'),
                        help='configuration file. Default: DEVRUN_CONFIG or /etc/devrun.cfg')
    res.add_argument('-v', '--verbose', dest='verbose', action='count', default=1,
                        help='increase chattiness')
    res.add_argument('-q', '--quiet', dest='verbose', action='store_const', const=0,
                        help='quiet operation')
    return res

class BaseCommand:
    help = None
    cfg = None
    amqp = None
    name = None

    def __init__(self, opt):
        self.opt = opt
        self.loop = opt.loop
        self.reg = Registry(self.loop)
        if getattr(self,'cfg',None) is None:
            self.cfg = load_cfg(opt.config)
        if isinstance(self.cfg,Mapping):
            self.name = self.cfg.get('global',{}).get('name',None)
        if self.name is None:
            self.name = os.path.splitext(os.path.basename(opt.config))[0]
        self.cmdname = self.__module__.rsplit('.',1)[1]

        self.loop.call_later(10,self.reg.done)

    async def start(self):
        if not isinstance(self.cfg,Mapping):
            return
        cfg = self.cfg.get('config',{})
        if 'amqp' in cfg:
            self.amqp = await qbroker.make_unit(self.name if self.cmdname == 'run' else '%s.%s'%(self.name,self.cmdname), amqp=cfg['amqp'])
    
        if 'etcd' in cfg:
            from etcd_tree import client
            self.etcd = await client(self.cfg, loop=self.loop)
            if 'root' in cfg['etcd']:
                self.etcd_root = await self.etcd.tree(cfg['etcd']['root'], immediate=None)
                self.tree = await self.etcd_root.subdir(*cfg.get('global',{}).get('prefix',"").split('.'), create=None,recursive=True)
                for k,v in cfg.items():
                    await self.tree.set(k,v)
            self.cfg = self.tree

    async def run(self):
        raise NotImplementedError("You need to override .run()")

    async def stop(self):
        if self.amqp is not None:
            await self.amqp.stop()

class cmd:
    def __getitem__(self, name):
        return import_string('devrun.cmd.'+name+'.Command')
cmd = cmd()


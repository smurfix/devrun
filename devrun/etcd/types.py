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
from traceback import print_exc

from qbroker.util import import_string
from etcd_tree import EtcRoot, EtcDir, EtcXValue, ReloadRecursive, \
    EtcString, EtcInteger, EtcFloat

import logging
logger = logging.getLogger(__name__)

# This file contains all "singleton" etcd directories, i.e. those with
# fixed names at the root of the tree

class recEtcDir:
    """an EtcDir mix-in which always loads its content up front"""
    @classmethod
    async def this_obj(cls, recursive, **kw):
        if not recursive:
            raise ReloadRecursive
        return (await super().this_obj(recursive=recursive, **kw))

    async def init(self):
        self.force_updated()
        await super().init()

class SubRun:
    """A mix-in class that start/stops all appropriate sub entries"""
    _started = False

    async def start(self):
        if self._started:
            return
        for v in self.values():
            if isinstance(v,EtcAwaiter):
                v = await v
            v = getattr(v,'start',None)
            if v is not None:
                await v()
        self._started = True

    async def stop(self):
        if not self._started:
            return
        for v in self.values():
            if isinstance(v,EtcAwaiter):
                v = await v
            v = getattr(v,'stop',None)
            if v is not None:
                await v()
        self._started = False

class MyRun:
    @property
    def job_done(self):
        def done_fn(f):
            if f.cancelled():
                return
            try:
                f.result()
            except Exception:
                print_exc()
        return done_fn

    async def run(self):
        raise RuntimeError("You need to define .run()")

    async def start(self):
        assert self._job is None
        self._job = asyncio.ensure_future(self._run)

    async def stop(self):
        if self._job is None:
            return
        self._job.cancel()
        self._job.add_done_function(self.job_done)
        self._job = None

    def has_update(self):
        super().has_update()
        if self._job is not None:
            self.root.queue_start(self)

class EvcRef(EtcXValue):
    """An entry referencing some other node"""
    _ref = None

    @property
    def ref(self):
        if self._ref is not None:
            return self._ref
        self._ref = self.root.tree.lookup(self.value)
        return self._ref

class EvcConfig(recEtcDir,EtcDir):
    """Singleton for /config"""
    pass
    # only here to preload the whole thing

class EvcDevice(MyRun, recEtcDir,EtcDir):
    """\
        Directory for /‹subsys›/‹name›.
        Will lookup the class to use by way of devrun.typ.‹subsys›.‹type›.Device,
        where ‹type› is the content of the …/type entry."""

    @classmethod
    async def this_obj(cls, parent=None,recursive=None, pre=None, **kw):
        if recursive is None:
            raise ReloadData
        m = 'devrun.typ.%s.%s.Device' % (self.parent.name,pre['type'])
    
    @classmethod
    def check_new_params(self, **params):
        pass
    def check_update_params(self, **params):
        for k,v in self:
            if k not in params:
                params[k] = v
        for k,v in list(params.items()):
            if v is None:
                del params[k]
        return self.check_params(**params)

class EvcType(SubRun,EtcDir):
    """/whatever"""
    async def init(self):
        self.register('*', cls=EvcDevice)
        await super().init()

class EvcRoot(SubRun,EtcRoot):
    """Singleton for etcd / (root)"""
    _start_q = None
    _start_job = None

    async def init(self):
        self.register('*', cls=EvcType)
        self.register('config', cls=EvcConfig)
        # preload these sub-trees
        try:
            await self['config']
        except KeyError: # does not exist yet
            pass
        await super().init()

    async def _start_run(self):
        while True:
            x = self._start_q.get()
            if x is None:
                return
            if x.parent._started:
                await x.stop()
                await x.start()

    def queue_start(self, x):
        self._start_q.put_nowait(x)

    async def start(self):
        assert self._start_job is None
        if self._start_q is None:
            self._start_q = asyncio.Queue(loop=self._loop)
        self._start_job = asyncio.ensure_future(self._start_run, loop=self._loop)
        await super().start()

    async def stop(self):
        if self._start_q:
            await self._start_q.push(None)
        if self._start_job is not None:
            await self._start_job
            self._start_job = None
        await super().stop()


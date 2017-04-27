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

"""A small object usable for recording some statistics"""

from asyncio import Lock
from time import time

class Stats:
    """This is a small object that aggregates statistics for serialized requests.
        It obeys the sync and async context manager protocols.
        The async version is locked."""

    def __init__(self,decay=0.05, loop=None):
        """decay: seconds for 10% decay of averages"""
        assert 0<decay<1
        self.decay = decay
        self.reset()
        self.lock = Lock(loop=loop)

    def start(self):
        t = time()
        if self.latest is not None:
            td = t-self.latest
            self.time_inter_msg = td*self.decay + self.time_inter_msg*(1-self.decay)
        self.latest = t

    def stop(self):
        td = time()-self.latest
        self.n += 1
        self.nt += td
        self.time_per_msg = td*self.decay + self.time_per_msg*(1-self.decay)

    def __enter__(self):
        assert not self.lock.locked()
        self.start()
    def __exit__(self,a,b,c):
        assert not self.lock.locked()
        self.stop()

    async def __aenter__(self):
        await self.lock.__aenter__()
        self.start()
    async def __aexit__(self,a,b,c):
        self.stop()
        await self.lock.__aexit__(a,b,c)

    def reset(self):
        self.first = time()
        self.latest = None
        self.time_per_msg = 0 # averaged
        self.time_inter_msg = 0 # averaged
        self.n = 0 # num requests
        self.nt = 0 # time spent processing requests

    @property
    def state(self):
        if self.latest is None:
            return dict(last_call=time()-self.first)
        t = time()
        return dict(
            n=self.n,
            t=t-self.first,
            load_all=self.nt/(t-self.first) if t>self.first else 0,
            time_all=t-self.first,
            load_now=self.time_per_msg/self.time_inter_msg if self.time_inter_msg else 0,
            last_call=t-self.latest,
            )


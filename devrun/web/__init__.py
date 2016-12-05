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

from aiohttp import web

from devrun.util import objects

import logging
logger = logging.getLogger(__name__)

async def hello(request):
    return web.Response(text="This is DevRun. You did not set up a handler for the root.")

class BaseView(web.View):
    path = None

class BaseExt:
    @classmethod
    async def start(cls, app):
        pass
    @classmethod
    async def stop(cls, app):
        pass

class FakeReq:
    """A very hacky way to test whether a resource exists on a path"""
    def __init__(self, path):
        self.__path = path
    @property
    def method(self):
        return 'GET'
    @property
    def rel_url(self):
        class _FR:
            @property
            def raw_path(s):
                return self._FakeReq__path
        return _FR()

class App:
    srv=None
    app=None
    handler=None

    def __init__(self, loop=None):
        self.loop = loop
        self.app = web.Application(loop=loop)

    async def start(self, bindto,port):
        for cls in objects('devrun.web', BaseExt):
            await cls.start(self.app)
        for view in objects("devrun.web",BaseView):
            if view.path is not None:
                print(view)
                self.app.router.add_route('*', view.path, view)

        r = FakeReq('/')
        r = await self.app.router.resolve(r)
        if getattr(r,'_exception',None) is not None:
            self.app.router.add_get('/', hello)

        self.handler = self.app.make_handler()
        self.srv = await self.loop.create_server(self.handler, bindto,port)
        logger.info('serving on %s', self.srv.sockets[0].getsockname())

    async def stop(self):
        if self.srv is not None:
            self.srv.close()
            await self.srv.wait_closed()
        if self.app is not None:
            for cls in objects('devrun.web', BaseExt):
                await cls.stop(self.app)
            await self.app.shutdown()
        if self.handler is not None:
            await self.handler.finish_connections(60.0)
        if self.app is not None:
            await self.app.cleanup()


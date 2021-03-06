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
import jinja2
import os
import aiohttp_jinja2
from hamlish_jinja import HamlishExtension

from . import BaseView,BaseExt

class JinjaExt(BaseExt):
    @classmethod
    async def start(self,app):
        env = aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),'templates')), extensions=[HamlishExtension])
        env.hamlish_file_extensions=('.haml',)
        env.hamlish_mode='debug'
        env.hamlish_enable_div_shortcut=True

        app.router.add_static('/static', os.path.join(os.path.dirname(__file__),'static'), name='static')
        env.filters['static'] = lambda x:app.router.named_resources()['static'].url_for(filename=x)

class RootView(BaseView):
    path = '/'
    @aiohttp_jinja2.template('main.haml')
    async def get(self):
        qb = self.request.app['devrun.cmd'].amqp
        x = await qb.rpc('info', _cmd='state',_subsys='charger')
        x = sorted(x.values(), key=lambda x: x['display_name'])
        return {'foo':'bar','charger':x, 'host':self.request.headers['host']}

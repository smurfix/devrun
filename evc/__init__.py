#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This file is part of evc, a controller framework for car chargers
##
## evc is Copyright © 2016 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.rst` for details,
## including optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP

__VERSION__ = (0,1,0)

import asyncio

def setup(_loop=None):
	global loop
	if loop is None:
		loop = _loop or asyncio.get_event_loop()
	elif _loop is not None:
		assert loop is _loop

loop = None # set by setup()

async def get_amqp(cfg, loop=None):
	import qbroker
	qbroker.setup()
	res = await qbroker.make_unit(loop=loop, **cfg)
	return res

async def get_etcd(cfg, loop=None):
	from etcd_tree.etcd import EtcClient
	res = EtcClient(**cfg['etcd'])
	await res.start()
	return res


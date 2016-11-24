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
import attr
from .util import typeof

class MODE:
	"""\
		Describes whether a controller needs intervention from EVC when a
		car is plugged in/out, or if it can run autonomously.
		"""
	AUTO = 'auto'
	MANUAL = 'manual'

	OFF = 'off' # emits an error code
	FAULT = 'fault' # dead

@attr.s
class AbstractCharger(object):
    name = attr.ib()
	mode = attr.ib(default=MODE.DEAD, validator=typeof(MODE), repr=False)
    power = attr.ib(default=0, validator=typeof(int,float))
    ready = attr.ib(default=False, validator=typeof(bool))

	connected = False
    
	async def init(self, broker):
		"""\
			Async part of device initialization.

			This code connects the charger to the message broker.
			"""
		self.broker = broker
		await broker.register_rpc_async("
    
	async def exit(self):
		"""\
			Async part of shutting down the connection to the charger in a
			controlled way. This may or may not be called before `.close`.
			"""
		pass
	
	def close(self):
		"""\
			Forcibly shuts down the connection to the back-end, if any
			exists, and frees any resources.
			"""
		pass

	### mode setting

	async def set_mode(self, mode):
		"""\
			Set the mode of the charger.
			"""
		self.mode = mode

	async def set_power(self, power):
		"""\
			Set the max power consumption of the charger.
			"""
		self.power = power

	async def set_ready(self, ready):
		"""\
			Allow charging. This is the dynamic 
			"""
		self.ready = ready

	### 
loop = None # set by setup()


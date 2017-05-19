#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This file is part of QBroker, an easy to use RPC and broadcast
## client+server using AMQP.
##
## QBroker is Copyright © 2016 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.rst` for details,
## including optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP

import asyncio
from qbroker.unit import Unit, CC_DATA, CC_MSG
from qbroker.util.tests import load_cfg
import signal
from pprint import pprint
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING,DESCENDING
from bson import SON

import logging
import sys
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

import sys
import asyncio
import inspect
from collections.abc import Mapping

from . import BaseCommand
from devrun.web import App

class Command(BaseCommand):
    "Collect data and park in mongodb"
    help = """\
dbmon
    -- collect data updates and store to mongodb
"""

    async def run(self, *args):
        self.loop = self.opt.loop
        if args:
            print("Usage: dbmon", file=sys.stderr)
            return 1

        cfg = self.cfg['config']['mongo']['data_logger']
        self.mongo = AsyncIOMotorClient(cfg['host'])
        self.coll = self.mongo[cfg['database']]
        self.db = self.coll[cfg['prefix']+'raw']
        await self.db.ensure_index((('type',ASCENDING),('name',ASCENDING),('timestamp',ASCENDING)),unique=True,name='primary')

        await self.amqp.register_alert_async('#', self.callback, durable='log_mysql', call_conv=CC_MSG)

        while True:
            await asyncio.sleep(9999,loop=self.loop)

    async def callback(self, msg):
        try:
            body = msg.data
            body['timestamp'] = msg.timestamp

            try:
                curs = self.db.find({'name': body['name'], 'type':body['type']}).sort('timestamp',DESCENDING)
            except KeyError:
                pprint(body)
                return
            doc = await curs.to_list(length=1)
            if doc:
                doc = doc[0]
                if doc['state'] != body['state']:
                    doc = None
            if doc:
                _id = doc['_id']
                res = await self.db.update({'_id': _id}, body)
            else:
                body['timestamp_first'] = body['timestamp']
                res = await self.db.insert_one(body)
            print(body['type'],body['name'],body['state'],res)

            #if properties.content_type == 'application/json' or properties.content_type.startswith('application/json+'):

        except Exception as exc:
            logger.exception("Problem processing %s", repr(body))


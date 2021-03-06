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

        await self.amqp.register_alert_async('update.charger', self.callback, durable='log_mongodb', call_conv=CC_MSG)

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
            body['change_a'] = 0
            body['change_b'] = 0
            doc = await curs.to_list(length=2)
            dr="update"
            if doc:
                if len(doc) > 1:
                    ts = doc[1]['timestamp']
                else:
                    ts = doc[0]['timestamp']
                doc = doc[0]
                _id = doc['_id']
                print("*",body['name'], doc['state'], doc['timestamp'], body['timestamp'])
                if doc['state'] != body['state']:
                    await self.db.update({'_id': _id},{"$set":{"change_b":1}})
                    dr = "state %s %s" % (doc['state'], body['state'])
                    doc = False
                elif doc.get('change_a',True) or (body['state'] == 'charging' and ts < body['timestamp']-5*60):
                    # We need another entry if the one we found was the first
                    # Also, when charging store an update every 5min
                    body['timestamp_first'] = doc.get('timestamp_first',doc['timestamp'])
                    if doc.get('change_a',True):
                        dr="change_a"
                    else:
                        dr="5min"
                    doc = None
            else:
                dr="notfound"
                doc = False
            # otherwise doc is an empty list
            if doc is False: # i.e. a real state change
                body['change_a'] = 1

            if doc:
                _id = doc['_id']
                res = await self.db.update({'_id': _id}, body)
            else:
                res = await self.db.insert_one(body)
            print(body['type'],body['name'],body['state'],body['change_a'],body['timestamp'],dr,res)

            #if properties.content_type == 'application/json' or properties.content_type.startswith('application/json+'):

        except Exception as exc:
            logger.exception("Problem processing %s", repr(body))


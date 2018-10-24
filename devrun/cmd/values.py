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

from . import BaseCommand
from datetime import datetime,timedelta

def date_conv(x):
    try:
        d = datetime.strptime(x,"%Y-%m-%d %H:%M")
    except ValueError:
        d = datetime.strptime(x,"%Y-%m-%d")
    return d

class Command(BaseCommand):
    "Read 15min load values from mongodb"
    help = """\
values date[/date] type[,type…]
    -- Find values in mongodb.
"""

    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        self.dbs = {}

    async def run(self, *args):
        self.loop = self.opt.loop
        if len(args) not in (1,2):
            print("Usage: values date[:date] [type[,type…]]", file=sys.stderr)
            return 1

        cfg = self.cfg['config']['mongo']['data_logger']
        self.mongo = AsyncIOMotorClient(cfg['host'])
        self.coll = self.mongo[cfg['database']].raw_meter
        fifteen=timedelta(0,15*60)

        dates = list(date_conv(x) for x in args[0].split('/'))
        d1 = dates[0]-fifteen
        d2 = dates[-1]+fifteen
        if len(args) > 1:
            stations = sorted(args[1].split(','))
        else:
            stations = sorted(self.cfg['devices']['meter'].keys())

        val={}
        print("Date Time",*stations, sep='\t')
        while d1 < d2:
            res = [d1]
            seen = 0
            for s in stations:
                m1 = await self.coll.find({'name':s, 'timestamp':{'$lte':d1.timestamp()}}).sort('timestamp',DESCENDING).to_list(length=1)
                m2 = await self.coll.find({'name':s, 'timestamp':{'$gt':d1.timestamp()}}).sort('timestamp',ASCENDING).to_list(length=1)
                if not m1 or not m2:
                    v=None
                else:
                    m1 = m1[0]
                    m2 = m2[0]
                    dlen = m2['timestamp']-m1['timestamp']
                    dpre = d1.timestamp()-m1['timestamp']
                    vdiff = m2['energy_total']-m1['energy_total']
                    v = m1['energy_total']+vdiff*dpre/dlen
                try:
                    vp = val.pop(s)
                except KeyError:
                    vp = None
                if v is not None:
                    val[s] = v
                if v and vp:
                    v -= vp
                    seen += 1
                else:
                    v = '-'
                res.append(v)
            d1 += fifteen
            if seen:
                print(*res, sep='\t')


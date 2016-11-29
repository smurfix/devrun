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

# run the balancing algorithm

from devrun.typ.power.limit import Device

class FakeCharger(object):
    def __init__(self, params):
        if 't' in params:
            self.charge_time = params['t']
        if 'meter' in params:
            self.meter = FakeMeter(params['meter'])
        self.params = params

    def update_available(self, a):
        self.params['a'] = a
    @property
    def A_max(self):
        return self.params['A_max']
    @property
    def A_min(self):
        return self.params['A_min']

class FakeMeter(object):
    def __init__(self, val):
        if isinstance(val,tuple):
            self.amp = val
            self.amp_max = max(val)
            self.amps = sum(val)
        else:
            self.amp = (val,)*3
            self.amp_max = val
            self.amps = 3*val

class FakeDevice(object):
    run = Device.update_available
    ramp_up = 5
    headroom = 2

    def __init__(self,params):
        self.params = params

    @property
    def A_max(self):
        return self.params['A_max']
    @property
    def charging(self):
        for v in self.params['chargers']:
            if not v['charging']:
                continue
            yield FakeCharger(v)
    @property
    def not_charging(self):
        for v in self.params['chargers']:
            if v['charging']:
                continue
            yield FakeCharger(v)

class TestBalancing:
    def validate(self,p,a):
        dev = FakeDevice(p)
        dev.run()
        assert tuple(x['a'] for x in p['chargers']) == a

    def test_basic_start(self):
        self.validate(dict(
            A_max=10,
            chargers=[
                dict(A_min=2, A_max=4, t=1, meter=1, charging=True),
                dict(A_min=2, A_max=4, t=1, meter=1, charging=True),
            ],
        ),(4,4))

    def test_basic_run(self):
        self.validate(dict(
            A_max=10,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
            ]
        ),(4,4))

    def test_limit_start(self):
        self.validate(dict(
            A_max=4,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
            ]
        ),(2,2))

    def test_limit_run(self):
        self.validate(dict(
            A_max=4,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
            ]
        ),(2,2))

    def test_limit_mix(self):
        self.validate(dict(
            A_max=4,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=4, t=10, meter=10, charging=True),
            ]
        ),(2,2))

    def test_nearlimit_mix(self):
        self.validate(dict(
            A_max=5,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=4, t=10, meter=10, charging=True),
            ]
        ),(2,3))

    def test_nearlimit_0(self):
        self.validate(dict(
            A_max=5,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=4, charging=False),
            ]
        ),(4,0))

    def test_nearlimit_1(self):
        self.validate(dict(
            A_max=4,
            chargers=[
                dict(A_min=2, A_max=5, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=5, charging=False),
            ]
        ),(4,0))

    def test_nearlimit_2(self):
        self.validate(dict(
            A_max=7,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, charging=False),
            ]
        ),(7,0))

    def test_nearlimit_3(self):
        self.validate(dict(
            A_max=8,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, charging=False),
            ]
        ),(6,2))

    def test_nearlimit_4(self):
        self.validate(dict(
            A_max=9,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, charging=False),
            ]
        ),(7,2))

    def test_dist_0(self):
        self.validate(dict(
            A_max=4+6+8+2,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=True),
                dict(A_min=2, A_max=8, charging=False),
            ]
        ),(4,6,8,2))

    def test_dist_1(self):
        self.validate(dict(
            A_max=4+6+8,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=True),
                dict(A_min=2, A_max=8, charging=False),
            ]
        ),(4,6,8,0))

    def test_dist_2(self):
        self.validate(dict(
            A_max=9,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=True),
                dict(A_min=2, A_max=8, charging=False),
            ]
        ),(2,3,4,0))

    def test_dist_3(self):
        self.validate(dict(
            A_max=3+4+5,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=True),
                dict(A_min=2, A_max=8, charging=False),
            ]
        ),(3,4,5,0))

    def test_dist_4(self):
        self.validate(dict(
            A_max=2+3+4+8,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=2.5, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=True),
                dict(A_min=2, A_max=8, t=1, meter=0, charging=True),
            ]
        ),(2,3,4,8))

    def test_dist_5(self):
        self.validate(dict(
            A_max=3+4+5+8,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=True),
                dict(A_min=2, A_max=8, t=1, meter=0, charging=True),
            ]
        ),(3,4,5,8))

    def test_dist_6(self):
        self.validate(dict(
            A_max=17,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=8, charging=True),
            ]
        ),(2,3,4,8))

    def test_dist_7(self):
        self.validate(dict(
            A_max=12,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=1, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=1.5, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=2, charging=True),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=True),
            ]
        ),(2,2,3,4))


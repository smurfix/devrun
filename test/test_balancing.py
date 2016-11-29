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

from devrun.typ.power.limit import Device,prio

class FakeCharger(object):
    _A = None

    def __init__(self, dev, params):
        if 't' in params:
            self.charge_time = params['t']
        if 'meter' in params:
            self.meter = FakeMeter(params['meter'])
        self.params = params
        self.power = dev

    def update_available(self, a):
        self.params['a'] = a
    @property
    def debug(self):
        return self.params.get('debug',False)
    @property
    def charging(self):
        return self.params['charging'] == 2
    @property
    def want_charging(self):
        return self.params['charging'] == 1
    @property
    def A_max(self):
        return self.params['A_max']
    @property
    def A_min(self):
        return self.params['A_min']
    @property
    def A(self):
        if self._A is not None:
            return self._A
        return (self.A_min+self.A_max)/2
    @A.setter
    def A(self,v):
        self._A = v
    def __str__(self):
        return "C:‹%s %s›" % (self._A, ','.join("%s=%s" % (k,v) for k,v in self.params.items()))

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
    _chargers = None

    def __init__(self,params):
        self.params = params
        self.prio = tuple(p() for p in prio)

    @property
    def A_max(self):
        return self.params['A_max']
    @property
    def charging(self):
        for v in self.chargers:
            if v.charging:
                yield v
    @property
    def want_charging(self):
        for v in self.chargers:
            if v.want_charging:
                yield v
    @property
    def not_charging(self):
        for v in self.chargers:
            if not v.charging and not v.want_charging:
                yield v
    @property
    def chargers(self):
        if self._chargers is None:
            self._chargers = tuple(FakeCharger(self,v) for v in self.params['chargers'])
            for i,c in enumerate(self._chargers):
                c.params['i'] = i
        return self._chargers

class TestBalancing:
    def validate(self,p,a):
        dev = FakeDevice(p)
        dev.run()
        assert tuple(x.A for x in dev.chargers) == a

    def test_basic_start(self):
        self.validate(dict(
            A_max=10,
            chargers=[
                dict(A_min=2, A_max=4, t=1, meter=1, charging=2),
                dict(A_min=2, A_max=4, t=1, meter=1, charging=2),
            ],
        ),(4,4))

    def test_basic_run(self):
        self.validate(dict(
            A_max=10,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
            ]
        ),(4,4))

    def test_limit_start(self):
        self.validate(dict(
            A_max=4,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
            ]
        ),(2,2))

    def test_limit_much(self):
        self.validate(dict(
            A_max=3,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=4, t=10, meter=2, charging=2),
            ]
        ),(3,0))

    def test_limit_run(self):
        self.validate(dict(
            A_max=4,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
            ]
        ),(2,2))

    def test_limit_mix(self):
        self.validate(dict(
            A_max=4,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=4, t=10, meter=10, charging=2),
            ]
        ),(2,2))

    def test_nearlimit_mix(self):
        self.validate(dict(
            A_max=5,
            chargers=[
                dict(A_min=2, A_max=5, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=5, t=10, meter=10, charging=2),
            ]
        ),(2,3))

    def test_nearlimit_i(self):
        self.validate(dict(
            A_max=5,
            chargers=[
                dict(A_min=2, A_max=5, t=1, meter=1, charging=2),
                dict(A_min=2, A_max=5, charging=1),
            ]
        ),(5,0))

    def test_nearlimit_0(self):
        self.validate(dict(
            A_max=5,
            chargers=[
                dict(A_min=2, A_max=4, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=4, charging=1),
            ]
        ),(3,2))

    def test_nearlimit_1(self):
        self.validate(dict(
            A_max=4,
            chargers=[
                dict(A_min=2, A_max=5, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=5, charging=1),
            ]
        ),(2,2))

    def test_nearlimit_2(self):
        self.validate(dict(
            A_max=7,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(5,2))

    def test_nearlimit_3(self):
        self.validate(dict(
            A_max=8,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(6,2))

    def test_nearlimit_4(self):
        self.validate(dict(
            A_max=9,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(7,2))

    def test_nearlimit_5(self):
        self.validate(dict(
            A_max=8,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, charging=0),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(6,0,2))

    def test_nearlimit_5a(self):
        self.validate(dict(
            A_max=9,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, charging=0),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(7,0,2))

    def test_nearlimit_5b(self):
        self.validate(dict(
            A_max=10,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, charging=0),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(8,0,2))

    def test_nearlimit_6(self):
        self.validate(dict(
            A_max=11,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, charging=0),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(8,0,3))

    def test_nearlimit_7(self):
        self.validate(dict(
            A_max=12,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, charging=0),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(8,0,4))

    def test_dist_0(self):
        self.validate(dict(
            A_max=4+6+8+2,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=2),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(4,6,8,2))

    def test_dist_1(self):
        self.validate(dict(
            A_max=3+4+5+2,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=2),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(3,4,5,2))

    def test_dist_2(self):
        self.validate(dict(
            A_max=2+3+4+2,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=2),
                dict(A_min=2, A_max=8, charging=1),
            ]
        ),(2.5,3,3.5,2))

    def test_dist_3(self):
        self.validate(dict(
            A_max=3+4+5,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=2),
                dict(A_min=2, A_max=8, charging=0),
            ]
        ),(3,4,5,0))

    def test_dist_4(self):
        self.validate(dict(
            A_max=2+3+4+8,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=1, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=2.5, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=2),
                dict(A_min=2, A_max=8, t=1, meter=0, charging=2),
            ]
        ),(2,3,4,8))

    def test_dist_5(self):
        self.validate(dict(
            A_max=3+4+5+8,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=2),
                dict(A_min=2, A_max=8, t=1, meter=0, charging=2),
            ]
        ),(3,4,5,8))

    def test_dist_6(self):
        self.validate(dict(
            A_max=17,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=2, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=4, charging=2),
                dict(A_min=2, A_max=8, t=10, meter=8, charging=2),
            ]
        ),(3,4,5,5))

    def test_dist_7(self):
        self.validate(dict(
            A_max=2+3+4+5,
            chargers=[
                dict(A_min=2, A_max=8, t=10, meter=1, charging=2), #2
                dict(A_min=2, A_max=8, t=10, meter=2, charging=2), #2+2
                dict(A_min=2, A_max=8, t=10, meter=3, charging=2), #2+4
                dict(A_min=2, A_max=8, t=10, meter=4, charging=2), #2+6
            ]
        ),(2,3,4,5))


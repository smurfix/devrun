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

from devrun.support import rev

fADC = 0.017

@rev
class RO:
    "EVCC output bits"
    X1 = 0
    X2 = 1
    K1 = 2
    K2 = 3
    K3 = 4
    CPpos = 5 # +12V
    CPneg = 6 # .12V

@rev
class RI:
    "EVCC input bits"
    E1 = 0
    E2 = 1

@rev
class RP:
    "PWM control values"
    A6 = 0
    A10 = 1
    A13 = 2
    A16 = 3
    A20 = 4
    A30 = 5
    A32 = 6
    A63 = 7
    A70 = 8
    A80 = 9
    default = 10
    min = 80
    max = 970
    not_allowed = 999

@rev
class RT:
    "EVCC commmands"
    # b == RT.reset_b
    reset = 0

    # returns version string
    firmware_version = 1

    # RM
    state = 2

    set_manual = 3

    # bits: RO
    output = 4
    set_output = 5
    clear_output = 6

    # voltage is result times fADC
    adc_cp_pos = 7
    adc_cp_neg = 8
    adc_cs = 9

    # bits: RI
    input = 10

    # Values: RP
    pwm = 11
    set_pwm = 12

    pwm_on = 13
    pwm_off = 14

    # Values: RP
    set_pwm_default = 15

    set_vent = 16 # b=111x
    vent = 17

    set_addr = 22 # b=111x
    addr = 23
    firmware_reset = 24 # b=reset_b; result will be >01

    stop_charge = 25
    set_auto = 25

    pwm_default = 26

    # device is available but doesn't (yet) charge
    set_brk = 27
    clear_brk = 28
    brk = 29

    # device is unavailable
    enter_Ax = 30
    leave_Ax = 31

    reset_b = 1111

@rev
class RM:
    A = 0
    B2 = 4
    C = 5
    D = 6
    Bx = 9
    B1 = 13
    Ax = 17
    firstErr = 32
    Err_CS = 33
    Err_AV = 35
    Err_Locker = 37
    Err_verification = 39
    transient = 64
    manual = 255
    charging = {B2,C,D,Bx}

class ReqReply:
    """encapsulate a request/reply exchanged while talking to the evc"""
    lead = None
    def __init__(self, nr,a,b=None):
        self.nr = nr
        self.a = a
        self.b = b

    def __str__(self):
        return self.bytes.decode('ascii').strip()

    @property
    def bytes(self):
        r = "%c%d %02d" % (self.lead,self.nr,self.a)
        if self.b is None:
            pass
        elif isinstance(self.b,int):
            r += ' %04d' % self.b
        else:
            r += ' ' + self.b
        r += '\r\n'
        return r.encode('ascii')

    @staticmethod
    def build(s):
        s = s.decode('ascii')
        if s[0] == Request.lead:
            c = Request
        elif s[0] == Reply.lead:
            c = Reply
        else:
            raise RuntimeError('Unknown input: '+repr(s))
        s = s[1:].strip('\n').strip('\r').strip(' ').split(' ')
        s[0] = int(s[0])
        s[1] = int(s[1])

        return c(*s)

class Request(ReqReply):
    "Encapsulates a request"
    lead = '!'
class Reply(ReqReply):
    "Encapsulates a reply"
    lead = '>'


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

import pytest

from devrun.support import timing

t = 123
def tm(x):
    global t
    t += x
def time():
    return t
timing.time = time

class TestBalancing:
    def setUp(self):
        self.old_time = timing.time
        timing.time = time

    def tearDown(self):
        timing.time = self.old_time

    def test_basic(self):
        s = timing.Stats()
        for i in range(30):
            s.start()
            tm(1)
            s.stop()
            tm(2)
        self.check(s)

    def test_with(self):
        s = timing.Stats()
        for i in range(30):
            with s:
                tm(1)
            tm(2)
        self.check(s)

    @pytest.mark.run_loop
    async def test_aiter(self, loop):
        s = timing.Stats(loop=loop)
        for i in range(30):
            async with s:
                tm(1)
            tm(2)
        self.check(s)

    def check(self,s):
        st = s.state
        assert 0.33 < st.pop('load_now') <= 0.34
        assert st == {
            'last_call': 3,
            'load_all': 1/3,
            'n': 30,
            't': 90,
            'time_all': 90,
            }

    
        


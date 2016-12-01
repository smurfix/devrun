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

"""\
This module implements a basic demo+test device which doesn't actually do
much, if anything.
"""

from devrun.typ import BaseType
from devrun.device import BaseDevice as _BaseDevice

class Type(BaseType):
    "Test. Do not use in production."
    help = "I am a test type. My devices do not do anything."

class BaseDevice(_BaseDevice):
    def cmd_ping(self,ping='pong'):
        """A little ping command"""
        return {'reply': ping}


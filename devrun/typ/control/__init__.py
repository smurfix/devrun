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
This module implements basic support for controllers.

"""

from devrun.typ import BaseType
from devrun.device import BaseDevice as _BaseDevice

import logging
logger = logging.getLogger(__name__)

class Type(BaseType):
    "This class is about controlling charging stations."
    help = "Station control."

class BaseDevice(_BaseDevice):
    def __init__(self, *a,**k):
        self.chargers = set()
        super().__init__(*a,**k)

    def register_charger(self, s):
        self.chargers.add(s)
        self.trigger()


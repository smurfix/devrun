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
This module implements all kind of bus-style connections.

Atypically, different devices here do not have the same API.
"""

from devrun.typ import BaseType
from devrun.device import BaseDevice # as _BaseDevice

class Type(BaseType):
    "This class describes bus systems to connect other devices to."
    help = "Bus."

#class BaseDevice(_BaseDevice):
#    pass

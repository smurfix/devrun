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

from . import BaseCommand
from devrun.util import objects, import_string

class Command(BaseCommand):
    "Basic command help"
    cfg = False # do not load

    help = """\
help
    -- list of commands
help ‹command›
    -- help text for that command
"""

    async def run(self, *args):
        if not args:
            for k in objects('devrun.cmd', BaseCommand):
                print("%s %s" % (k.__module__.rsplit('.',1)[1],
                    k.__doc__.split('\n',1)[0] if k.__doc__ else ''))
        else:
            k = import_string('devrun.cmd.%s.Command' % ('.'.join(args),))
            print(k.help)

# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This file is part of evc, a comprehensive controller and monitor for
## chargers of electric vehicles.
##
## evc is Copyright © 2016 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.rst` for details,
## including optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP

import sys

from . import BaseCommand
from evc.util import objects, import_string
from evc.typ import BaseType
from evc.etcd.types import EvcDevice

class Command(BaseCommand):
    "Shows groups and types of entries EVC knows about"
    cfg = False
    help = """\
type
    -- list of groups
type ‹group› 
    -- group's description; list types within that group
type ‹group› ‹type›
    -- type's description; list of parameters for that type
"""

    async def run(self, *args):
        if not args:
            ks = []
            ks_len = 6
            for k in objects('evc.typ', BaseType):
                n = k.__module__.rsplit('.',1)[1]
                d = k.__doc__.split('\n',1)[0] if k.__doc__ else ''
                ks_len = max(ks_len,len(n))
                ks.append((n,d))
            for n,d in sorted(ks):
                print("%%-%ds %%s" % (ks_len,) % (n,d))
        elif len(args) == 1:
            k = import_string('evc.typ.%s.Type' % (args[0],))
            print(k.help)
            print('\nKnown types:\n')

            for k in objects('evc.typ.'+args[0], EvcDevice):
                print("""\
*** %s
%s
""" % (k.__module__.rsplit('.',1)[1],k.help))

        elif len(args) == 2:
            k = import_string('evc.typ.%s.%s.Device' % (args[0],args[1]))
            print(k.help)

            ks = []
            ks_nlen = 6
            ks_tlen = 10

            for n,v in k._types.items():
                t = v[0].__name__.replace('Etc','').lower()
                ks_nlen = max(ks_nlen,len(n))
                ks_tlen = max(ks_tlen,len(t))
                ks.append((n,t,v.doc or ''))
            if ks:
                print('\nKnown parameters:\n')
                f = '%%-%ds %%-%ds %%s' % (ks_nlen,ks_tlen)
            
                for n,v,d in sorted(ks):
                    print(f % (n,v,d))
            else:
                print('\nNo parameters.')
        else:
            print("Usage: type [‹group› [‹type›]]", file=sys.stderr)
            return 1

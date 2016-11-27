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

class rev:
    """\
        Add a reverse-lookup via dict.

        Usage:

            >>> class X(rev):
            ...        A=12
            >>> X.A
            12
            >>> X[12]
            'A'

    """
    _items = None
    @classmethod
    def __getitem__(cls,x):
        if cls._items is None:
            cls._items = {}
            for k,v in vars(cls).items():
                if not k.startswith('_') and isinstance(v,(int,str)):
                    cls._items[v] = k
        return cls._items[x]


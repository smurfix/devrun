#!/usr/bin/env python
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

from importlib import import_module
import os

def typeof(*t):
    def check(_a,_b,v):
        if not isinstance(v,t):
            raise RuntimeError("Type mismatch: %s is not a %s (%s %s)" % (repr(v),repr(t),repr(_a),rept(_b)))
    return check

def import_string(name):
    from importlib import import_module
    """Import a module, or resolve an attribute of a module."""
    name = str(name)
    try:
        return import_module(name)
    except ImportError as ierr:
        if '.' not in name:
            raise
        module, obj = name.rsplit('.', 1)
        module = import_string(module)
        try:
            return getattr(module,obj)
        except AttributeError:
            raise ierr from None
            raise ImportError(name) from None

def objects(module, cls, immediate=False,direct=False,filter=lambda x:True):
    import pkgutil
    """\
        List all subclasses of a given class in a directory.

        If @immediate is set, only direct subclasses are returned.
        If @direct is set, modules in subdirectories are ignored.
        """
    def _check(m):
        try:
            if isinstance(m,str):
                m = import_module(m)
        except ImportError as ex:
            raise # ImportError(m) from ex # pragma: no cover
            # not going to ship a broken file for testing this
        else:
            try:
                syms = m.__all__
            except AttributeError:
                syms = dir(m)
            for c in syms:
                c = getattr(m,c,None)
                if isinstance(c,type) and \
                        ((c.__base__ is cls) if immediate else (c is not cls and issubclass(c,cls))):
                    if filter(c):
                        yield c

    if isinstance(module,str):
        from qbroker.util import import_string
        module = import_string(module)
    yield from _check(module)
    try:
        for a,b,c in pkgutil.walk_packages((os.path.dirname(module.__file__),), module.__name__+'.'):
            if direct and a.path != module.__path__[0]:
                continue
            yield from _check(b)
    except ImportError as err:
        if err.args and err.args[0].endswith("is not a package"):
            yield from _check(module)
        else:
            raise

def load_cfg(cfg):
    from yaml import safe_load
    """load a config file"""

    with open(cfg) as f:
        cfg = safe_load(f)

    return cfg


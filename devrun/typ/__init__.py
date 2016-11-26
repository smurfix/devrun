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

class BaseType:
	"""Helper class for listing device types"""
	help = None # multi-line help text

class NotGiven:
	pass

class Verified:
	"""\
		Mix-in which supplies an async verify(**params) method.

		The default implementation dispatches each value to verify_‹key› methods.
		"""
	_verify_required = ()

	async def verify(self, type=NotGiven, **params):
		if type is not NotGiven:
			raise SyntaxError("You can't change a device's type.")
		for k in self._verify_required:
			if params.get(k,None) is None:
				raise SyntaxError("Parameter ‹%s› is required." % (k,))
		for k,v in params.items():
			r = getattr(self,'verify_'+k)(v)
			if r is not None:
				await r
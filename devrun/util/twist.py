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

from twisted.internet.defer import Deferred

if not hasattr(Deferred,'asFuture'):
    def asFuture(self, loop):
        """
        Adapt a L{Deferred} into a L{asyncio.Future} which is bound to C{loop}.

        @note: converting a L{Deferred} to an L{asyncio.Future} consumes both
            its result and its errors, so this method implicitly converts
            C{self} into a L{Deferred} firing with L{None}, regardless of what
            its result previously would have been.

        @since: Twisted NEXT

        @param loop: The asyncio event loop to bind the L{asyncio.Future} to.
        @type loop: L{asyncio.AbstractEventLoop} or similar

        @param deferred: The Deferred to adapt.
        @type deferred: L{Deferred}

        @return: A Future which will fire when the Deferred fires.
        @rtype: L{asyncio.Future}
        """
        try:
            createFuture = loop.create_future
        except AttributeError:
            from asyncio import Future
            def createFuture():
                return Future(loop=loop)
        future = createFuture()
        def checkCancel(futureAgain):
            if futureAgain.cancelled():
                self.cancel()
        def maybeFail(failure):
            if not future.cancelled():
                future.set_exception(failure.value)
        def maybeSucceed(result):
            if not future.cancelled():
                future.set_result(result)
        self.addCallbacks(maybeSucceed, maybeFail)
        future.add_done_callback(checkCancel)
        return future
    Deferred.asFuture = asFuture

if not hasattr(Deferred,'fromFuture'):
    @classmethod
    def fromFuture(cls, future):
        """
        Adapt an L{asyncio.Future} to a L{Deferred}.

        @note: This creates a L{Deferred} from a L{asyncio.Future}, I{not} from
            a C{coroutine}; in other words, you will need to call
            L{asyncio.async}, L{asyncio.ensure_future},
            L{asyncio.AbstractEventLoop.create_task} or create an
            L{asyncio.Task} yourself to get from a C{coroutine} to a
            L{asyncio.Future} if what you have is an awaitable coroutine and
            not a L{asyncio.Future}.  (The length of this list of techniques is
            exactly why we have left it to the caller!)

        @since: Twisted NEXT

        @param future: The Future to adapt.
        @type future: L{asyncio.Future}

        @return: A Deferred which will fire when the Future fires.
        @rtype: L{Deferred}
        """
        def adapt(result):
            try:
                extracted = result.result()
            except:
                extracted = failure.Failure()
            adapt.actual.callback(extracted)
        futureCancel = object()
        def cancel(reself):
            future.cancel()
            reself.callback(futureCancel)
        self = cls(cancel)
        adapt.actual = self
        def uncancel(result):
            if result is futureCancel:
                adapt.actual = Deferred()
                return adapt.actual
            return result
        self.addCallback(uncancel)
        future.add_done_callback(adapt)
        return self
    Deferred.fromFuture = fromFuture


=================
Setting up DevRun
=================

Create a configuration file:

    config:
      amqp:
        server:
          host: localhost
          login: guest
          password: guest
          virtualhost: /moat
      … whatever other global configuration you need
    devices:
      test:
        pling:
          type: ping
          config:
            interval: 1.5
      

-----------
Basic usage
-----------

The `devrun` command supports a couple of sub-commands.

type
====

Lists the available device classes and what they're for.

type ‹class›
============

Lists the available types in a class. For instance:

    type test

will show what kind of test devices are available.

type ‹class› ‹kind›
===================

shows detailed information about this kind of device, including the parameters you can
set for it.

    type test ping

will tell you that it recognizes a delay parameter:

    Parameters:

    config.interval float    Interval between 'foo' pings

type ‹class› ‹kind› ‹name›
==========================

get
===


run
===

Starts up all devices.

Any uncaught error will result in a stack trace and a (clean) termination of the whole stack.

Hopefully.

web
===

Starts a web server, based on `aiohttp`.

Routes are loaded dynamically: simply add modules below `devrun.web`
which subclass `devrun.web.BaseView`. For system-wide startup and teardown,
subclass `devrun.web.BaseExt` and override the `start` and or `stop` class
methods.

See the `evc` branch for an example (a dynamically-updated status page
using Jinja2 templates and websockets).

help
====

Print basic (sub)command usage.


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

will tell you that it requires a ModBus-TCP gateway and a device address:

    Parameters:

    bus: ‹host› or ‹host:port›  address of a ModBus/TCP gateway
    bus_addr: ‹int›             device address on that bus
    phase: ‹int›                phase to measure. 0:all of them

run
===

Starts up all devices.

Any uncaught error will result in a stack trace and a (clean) termination of the whole stack.

help
====

Print basic (sub)command usage.


data structure
==============

DevRun uses YAML to store state and persistent data, including system configuration.

Informally, there are subdirectories for each type of device, with named
subdirectories using a ``type`` to describe the actual instance. Thus, a
typical (albeit incomplete) data structure for managing an array of
chargers for electric cars would be:

    config
        amqp
            host: localhost
    devices
        charger
            s1
                type: abl
                config
                    meter: m1
                    bus: s123
                    address: 1
                    mode: TODO
                    A_max: 32
        meter
            m1
                config
                    type: sdm630
                    bus: mb1
                    address: 1
                    power: p1
        control
            // TODO
            master
                type: TODO
                config
                    xxx
        bus
            s123
                type: abl
                config
                    remote: host2:50485
                    // or local: /dev/rs485-1
            mb1
                type: modbus
                config
                    remote: host1:502
                    local: /dev/rs485-2
                    speed: 9600
        reader
            r1
                type: TODO
                config
                    charger: s1
        power
            p1
                type: limit
                config
                    A_max: 100
        front
            // TODO
            plugsurfing
                type: plugsurfing
                config
                    chargers: *
            local
                type: manual
                config
                    chargers: *

* charger

  A back-end responsible for one charging station. May be equipped with a
  beeper and/or some indicator lights.

* meter

  Measures one charger's energy consumption and current(s).

* bus

  A connection to a physical bus which controls one or more chargers by way
  of a local bus interface. Not used for chargers with a TCP/IP interface.

* control

  Responsible for distributing power to charging stations.

* front

  Front-end for one or more controllers.

* reader

  Card reader, associated with one or more chargers. A reader may be
  equipped with a display, beeper, and/or indicator lights.


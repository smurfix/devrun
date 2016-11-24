ETCD data structure
===================

EVC uses `etcd_tree`_ to store state and persistent data, including system configuration.
``etcd`` is not used for communication or job control.

Stored data are described by commented `JSON Schema`_ documents.
The top level is described in the directory ``schema/etcd/root.json``.

Informally, there are subdirectories for each type of device, with named
subdirectories using a ``type`` to describe the actual instance. Thus, a
typical (albeit incomplete) data structure would be

    some…root
        charger
            s1
                type: EVCC_manual
                config
                    meter: m1
                    conn: s123
                    conn_port: 1
                    mode: OFF
                    A_max: 32
        meter
            m1
                config
                    type: SDM630
                    bus: host1:502
                    bus_addr: 1
        control
            master
                type: builtin
                config
                    xxx
        conn
            s123
                type: rs485
                config
                    remote: host2:50485
                    local: /dev/rs485-1
        reader
            r1
                type: TODO
                config
                    charger: s1
        front
            plugsurfing
                type: plugsurfing
                config
                    chargers: *
            local
                type: manual
                config
                    chargers: *

Typically, one would configure a distinct root per physical location.
Thus, there is no need for further subdivision of hierarchy.

* charger

  A back-end responsible for one charging station. May be equipped with a
  beeper and/or some indicator lights.

* meter

  Measures one charger's energy consumption and current(s).

* conn

  A connection to a physical bus which controls one or more chargers by way
  of a local bus interface. Not used for chargers with a TCP/IP interface.

* control

  Responsible for distributing power to charging stations.

* front

  Front-end for one or more controllers.

* reader

  Card reader, associated with one or more chargers. A reader may be
  equipped with a display, beeper, and/or indicator lights.

.. _etcd_tree: https://github.com/M-o-a-T/etcd_tree/

.. _JSON Schema: http://json-schema.org/


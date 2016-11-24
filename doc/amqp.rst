AMQP messages
=============

EVC uses `qbroker`_ to interface to an AMQP bus.
It also uses AMQP for all its internal communication.

All messages are described by commented `JSON Schema`_ documents. Messages
are sent with a routing key of ``evc.‹type›.‹name›``; the top level is
described in the directory ``schema/‹type›/‹name›.‹kind›.json``.

Possible values for ``‹type›`` are

* charger

  A back-end responsible for one charging station. May be equipped with a
  beeper and/or some indicator lights.

* meter

  Measures one charger's energy consumption and current(s).

* control

  Responsible for distributing power to charging stations.

* front

  Front-end for one or more controllers.

* reader

  Card reader, associated with one or more chargers. A reader may be
  equipped with a display, beeper, and/or indicator lights.

``‹kind›`` is one of

* rpc

  A remote procedure call request.

* reply

  The reply associated with the request of the same name.

* alert

  Some broadcast message.

* replies

  Any replies triggered by an ``alert`` message.


.. _qbroker: https://github.com/M-o-a-T/qbroker/

.. _JSON Schema: http://json-schema.org/


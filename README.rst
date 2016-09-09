EVC -- Electric Vehicle Charger
===============================

This program (and associated module) interfaces frontends and backends for
charging electric vehicles.

Supported frontends:

* command-line interface, via AMQP messages

* CCMS charge manager, ABL Sursum

* built-in charge manager

Supported backends:

* dummy charger, controlled via AMQP (for testing)

* EVCC: charge controller, ABL Sursum (autonomous mode)

* EVCC: charge controller, ABL Sursum (manual mode)

Supported meters:

* SDM630, via Modbus

Supported accounting protocols:

* Plugsurfing

* AMQP messaging


.. include:: README.rst

EVCC: charge controller
-----------------------

This controller uses a half-duplex RS485 interface at 38400 baud.
It supports one-phase or three-phase AC chargers at up to whatever amperage
your hardware can deliver, up to 80A per phase ("hard" protocol limit).
Typical cars take at most 32A at 230V, corresponding to 22 kW.

The RS485 interface has no collision detection or avoidance.

CCMS: charge manager
--------------------

This is a small box, also with RS485. Without EVC, this box is connected
to the EVCC in automatic mode. It can be configured with the max power
level per charger; the available power is distributed equally among all
connected vehicles.

The RS485 interface is 38400 baud (obviously) and has strict timing
requirements. There is no collision detection or avoidance.

EVC interprets the commands from this controller and translates them to
its internal format.


DevRun -- run code for devices
==============================

This program controls running a variety of devices,
described by a common configuration file.

DevRun is intended to be a quick-and-dirty framework for managing a system
of devices. The author uses it for controlling "dumb" chargers for electric
cars, integrating the charger, power meter, web frontend, authorisation
management, accounting, and other components. DevRun reads the global and
device configuration, starts asynchronous jobs for all instances (ensuring
correct startup order), and provides a common interface for messaging and
object storage.

Currently, there are modules for

  * modbus power meters
    * SDM630
	* UMG96
  * ABL/Sursum EVC chargers
  * power supply, distributing available power among chargers intelligently
    * simple current limit
	* power limit (delta between current usage and max capacity)

There's also an independent modbus gateway module which uses pymodbus to
multiplex multiple units to remote modbus-TCP devices. The author uses that
to talk to dumb modbus meters which only do one concurrent TCP connection.

DevRun requires Python 3.5. It uses asyncio natively.

Future plans include persistent distributed storage (etcd), interfacing to
chargers with OCPP, "manual" mode for ABL/Sursum chargers, and modular
access control.


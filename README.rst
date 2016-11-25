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

DevRun requires Python 3.5. It uses asyncio natively.


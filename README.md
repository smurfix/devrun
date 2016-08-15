CCMS312 distributor
===================

This program connects to multiple sockets, typically with RS422 interfaces
behind them. The first such interface is assumed to be connected to a
CCMS312 charge manager from ABL Sursum, the others to buses with charging
station managers (EVCC).

The EVCCs need to be pre-programmed with distinct bus addresses (1-8).
To do this, connect RS422 at 38400 baud and do:

	!0 03
	>0 03
	!0 22 111<n>
	><n> 22
	!<n> 25
	><n> 25

You type the '!' lines; the station replies with the '>' lines. Replace
'<n>' with the ID you want to assign.


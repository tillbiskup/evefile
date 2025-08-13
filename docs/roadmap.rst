=======
Roadmap
=======

A few ideas how to develop the project further, currently a list as a reminder for the main developers themselves, in no particular order, though with a tendency to list more important aspects first:


For version 0.1
===============

* API somewhat similar to the legacy evefile package, but without C++ objects shining through
* Support of monitors (including converting timestamps in position counts)
* Simplify average and interval channel data (no raw data available)
* Fill all data vectors for average and interval channel data and include in DataFrame

  * Move fill methods to data classes? Might work.

* ``show_info()`` method for data objects providing human-readable details of an individual data object, similar to :meth:`evefile.boundaries.evefile.EveFile.show_info`


For version 0.2
===============

* Readd more complex data types for SDDs and cameras?


Todos
=====

A list of todos, extracted from the code and documentation itself, and only meant as convenience for the main developers. Ideally, this list will be empty at some point.

.. todolist::

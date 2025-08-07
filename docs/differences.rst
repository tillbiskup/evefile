.. _evedata: https://evedata.docs.radiometry.de/

======================
Differences to evedata
======================

*An overview of the differences to evedata, and an explanation why evefile exists, anyway.*


Overview: Differences to evedata
================================

In short:

* (Much) less abstractions -- making implementation much easier
* No processing of the scan description (thus lacking a lot of information)



Why evefile? Why not just evedata?
==================================

The simple answer: urgent needs and lack of resources. `evedata`_ is under active development, but due to its inherently larger complexity compared to evefile, a first usable release will still take a bit of time (as of 08/2025). The currently available Python interfaces to the eveH5 files are unsatisfying, but there is a rather urgent need to transition from IDL to Python. Hence, a somewhat conveniently usable interface should exist.


Differences to previous interfaces
==================================

In short:

* Native Python
* More intuitive interface
* More abstractions (*e.g.*, mapping of options from snapshot to data classes)
* Direct access to monitor data -- including mapping of timestamps to position counts

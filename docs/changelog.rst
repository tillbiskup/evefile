=========
Changelog
=========

This page contains a summary of changes between the official evefile releases. Only the biggest changes are listed here. A complete and detailed log of all changes is available through the `GitHub Repository Browser <https://gitlab1.ptb.de/eve/eve-file-py>`_.


Version 0.1.0
=============

Not yet released

* First public release

* ...


Version 0.1.0-rc.2
==================

Released 2025-08-19

New features
------------

* :meth:`evefile.entities.data.Data.get_dataframe` to get a Pandas DataFrame for an individual data object.
* :meth:`evefile.entities.data.MeasureData.join` for harmonising data (including all data attributes) to a given list of positions.

  * Hopefully, join modes are implemented correctly this time. ;-)

* All additional data attributes of, *e.g.* :class:`evefile.entities.data.AverageChannelData`, will trigger data import on first access.


Version 0.1.0-rc.1
==================

Released 2025-08-12

* First public pre-release (release candidate)
* Basic import of eveH5 files down to eveH5 version 5
* Mapping of HDF5 datasets to data objects
* Dataset/array joining (aka "fill modes")

=========
Changelog
=========

This page contains a summary of changes between the official evefile releases. Only the biggest changes are listed here. A complete and detailed log of all changes is available through the `GitHub Repository Browser <https://gitlab1.ptb.de/eve/eve-file-py>`_.


Version 0.2.0
=============

Not yet released


New features
------------

* Support for array detectors, such as MCAs, via classes :class:`evefile.entities.data.ArrayChannelData`, :class:`evefile.entities.data.MCAChannelData`, :class:`evefile.entities.data.MCAChannelROIData`, and corresponding metadata classes.


Version 0.1.0
=============

Released 2025-09-12

* First public release


New features
------------

* :meth:`evefile.boundaries.evefile.EveFile.get_monitors` to get a (list of) monitor(s) converted into datasets with timestamps mapped to position counts.
* :meth:`evefile.boundaries.evefile.EveFile.get_snapshots` to get an overview of all snapshots as a single Pandas DataFrame.
* Joining takes (mapped) monitors into account if provided.
* New parameter ``include_monitors`` in :meth:`evefile.boundaries.evefile.EveFile.get_joined_data` and :meth:`evefile.boundaries.evefile.EveFile.get_dataframe` to include all (mapped) monitor datasets.


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

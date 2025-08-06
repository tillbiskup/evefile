"""

*High-level Python object representation of eveH5 file contents.*

.. sidebar:: Contents

    .. contents::
        :local:
        :depth: 1

This module provides a high-level representation of the contents of an eveH5
file. Being a high-level, user-facing object representation, technically
speaking this module is a facade. The corresponding resource
(persistence-layer-facing interface) would be the :mod:`eveh5
<evefile.boundaries.eveh5>` module.


Overview
========

A first overview of the classes implemented in this module and their
hierarchy is given in the UML diagram below.


.. figure:: /uml/evefile.boundaries.evefile.*
    :align: center

    Class hierarchy of the :mod:`evefile.boundaries.evefile` module,
    providing the facade (user-facing interface) for an eveH5 file.
    Basically, it inherits from :class:`evefile.entities.file.File`
    and adds behaviour. Most of this behaviour is contributed by the various
    modules of the :mod:`controllers <evefile.controllers>`
    subpackage.


Key aspects
===========

While the :mod:`evefile <evefile.boundaries.evefile>` module is the
high-level interface (facade) of the ``evefile`` package,
it is still, from a functional viewpoint, close to the actual eveH5 files,
providing a faithful representation of all information contained in an eveH5
(and SCML) file. Nevertheless, it is clearly an abstraction from the actual
data files. Hence, the key characteristics of the module are:

* Stable interface to eveH5 files, regardless of their version.

  * Some features may only be available for newer eveH5 versions, though.

* Powerful abstractions on the device level.

  * Options to devices appear as attributes of the device objects, not as
    separate datasets.

* Actual **data are loaded on demand**, not when loading the file.

  * This does *not* apply to the metadata of the individual datasets.
    Those are read upon reading the file.
  * Reading data on demand should save time and resources, particularly
    for larger files.
  * Often, you are only interested in a subset of the available data.


Usage
=====

Loading the contents of a data file of a measurement may be as simple as:

.. code-block::

    evefile = EveFile(filename="my_measurement_file.h5")
    evefile.load()


Internals: What happens when reading an eveH5 file?
===================================================

Reading an eveH5 file is not as simple as reading contents of an HDF5 file
and present its contents as Python object hierarchy. At least, if you would
like to view, process, and analyse your data more conveniently, you should
not stop here. The idea behind the ``evefile`` package, and in parts behind
the :class:`EveFile` class, is to provide you as consumer of the data with
powerful abstractions and structured information. To this end, a series of
steps are necessary:

* Read the eveH5 file (actually, an HDF5 file).
* Get the correct :class:`VersionMapper
  <evefile.controllers.version_mapping.VersionMapper>` class.
* Map the file contents to the proper data structures provided by the
  ``evefile`` package.


Module documentation
====================

"""

import logging

from evefile.entities.file import File


logger = logging.getLogger(__name__)


class EveFile(File):
    """
    High-level Python object representation of eveH5 file contents.

    This class serves as facade to the entire :mod:`evefile`
    subpackage and provides a rather high-level representation of the
    contents of an individual eveH5 file.

    Individual measurements are saved in HDF5 files using a particular
    schema (eveH5). Besides file-level metadata, there are log messages,
    a scan description (originally an XML/SCML file), and the actual data.

    The data are organised in three functionally different sections: data,
    snapshots, and monitors.


    Attributes
    ----------
    metadata : :class:`evefile.entities.file.Metadata`
        File metadata

    log_messages : :class:`list`
        Log messages from an individual measurement

        Each item in the list is an instance of
        :class:`evefile.entities.file.LogMessage`.

    data : :class:`dict`
        Data recorded from the devices involved in the scan.

        Each item is an instance of
        :class:`evedata.evefile.entities.data.Data`.

    snapshots : :class:`dict`
        Device data recorded as snapshot during a measurement.

        Only those device data that are not options belonging to any of
        the devices in the :attr:`data` attribute are stored here.

        Each item is an instance of
        :class:`evefile.entities.data.Data`.

    monitors : :class:`dict`
        Device data monitored during a measurement.

        Each item is an instance of
        :class:`evefile.entities.data.Data`.

    position_timestamps : :class:`evefile.entities.data.TimestampData`
        Timestamps for each individual position.

        Monitors have timestamps (milliseconds since start of the scan)
        rather than positions as primary quantisation axis. This object
        provides a mapping between timestamps and positions and can be used
        to map monitor data to positions.


    Parameters
    ----------
    filename : :class:`str`
        Name of the file to be loaded.


    Raises
    ------
    exception
        Short description when and why raised


    Examples
    --------
    Loading the contents of a data file of a measurement may be as simple as:

    .. code-block::

        evefile = EveFile(filename="my_measurement_file.h5")
        evefile.load()


    .. todo::
        Shall the constructor be slightly changed, so that loading a file
        becomes standard? May be more convenient for the users. To retain
        testability, one could think of an additional parameter, like so:

        .. code-block::

            def __init__(self, filename="", load=True):
                ...
                if load:
                    self.load()

        This would just need an (anyway necessary) check for the filename
        to be present in the :meth:`load` method.


    """

    def __init__(self, filename=""):
        super().__init__()
        self.filename = filename

    @property
    def filename(self):
        """
        Name of the file to be loaded.

        Returns
        -------
        filename : :class:`str`
            Name of the file to be loaded.

        """
        return self.metadata.filename

    @filename.setter
    def filename(self, filename=""):
        self.metadata.filename = filename

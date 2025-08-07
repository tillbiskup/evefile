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
from evefile.boundaries.eveh5 import HDF5File
from evefile.controllers import version_mapping


logger = logging.getLogger(__name__)


class EveFile(File):
    """
    High-level Python object representation of eveH5 file contents.

    This class serves as facade to the entire ``evefile`` package and provides
    a rather high-level representation of the contents of an individual
    eveH5 file.

    Individual measurements are saved in HDF5 files using a particular
    schema (eveH5). Besides file-level metadata, there are log messages
    and the actual data.

    The data are organised in three functionally different sections: data,
    snapshots, and monitors. While the "data" section contains the data of
    motor axes moved and detector channels read out during the scan,
    the "snapshot" section contains values at distinct times (usually at
    the very beginning of a scan), usually of more devices than used in
    the scan. The "monitors" section contains data of all those devices
    monitored during the scan, meaning that only changes in values are
    recorded, together with their timestamp (rather than position count).

    Values from axes contained in the "snapshot" section are used for data
    joining, while all other values can be regarded as either options
    of individual devices or telemetry data for the setup. All values from
    the "monitors" section are strictly telemetry data for the setup.


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

        The keys of the dictionary are the (guaranteed to be unique) HDF
        dataset names, not the "given" names usually familiar to the users.
        Use the :meth:`get_data` method to retrieve data objects by their
        "given" name.

        Each item is an instance of
        :class:`evefile.entities.data.Data`.

    snapshots : :class:`dict`
        Device data recorded as snapshot during a measurement.

        Only those device data that are not options belonging to any of
        the devices in the :attr:`data` attribute are stored here.

        The keys of the dictionary are the (guaranteed to be unique) HDF
        dataset names, not the "given" names usually familiar to the users.

        Each item is an instance of
        :class:`evefile.entities.data.Data`.

    monitors : :class:`dict`
        Device data monitored during a measurement.

        The keys of the dictionary are the (guaranteed to be unique) HDF
        dataset names, not the "given" names usually familiar to the users.

        Each item is an instance of
        :class:`evefile.entities.data.MonitorData`.

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

    def load(self):
        """Load contents of an eveH5 file containing data."""
        self._read_and_map_eveh5_file()

    def _read_and_map_eveh5_file(self):
        eveh5 = HDF5File()
        eveh5.read_attributes = True
        eveh5.close_file = False
        eveh5.read(filename=self.metadata.filename)
        mapper_factory = version_mapping.VersionMapperFactory()
        mapper = mapper_factory.get_mapper(eveh5)
        mapper.map(source=eveh5, destination=self)
        eveh5.close()

    def get_data(self, name=None):
        """
        Retrieve data objects by name.

        While generally, you can get the data objects by accessing the
        :attr:`data <evefile.entities.file.File.data>` attribute directly,
        there, they are stored using their HDF5 dataset name as key.
        Usually, however, data are accessed by their "given" name.

        Parameters
        ----------
        name : :class:`str` | :class:`list`
            Name or list of names of data to retrieve

        Returns
        -------
        data : :class:`evefile.entities.data.Data` | :class:`list`
            Data object(s) corresponding to the name(s).

            In case of a list of data objects, each object is of type
            :class:`evefile.entities.data.Data`.

        """
        data = []
        names = {item.metadata.name: key for key, item in self.data.items()}
        if isinstance(name, (list, tuple)):
            for item in name:
                data.append(self.data[names[item]])
        else:
            data.append(self.data[names[name]])
        if len(data) == 1:
            data = data[0]
        return data

    def get_data_names(self):
        """
        Retrieve "given" names of data objects.

        Data are stored in the :attr:`data <evefile.entities.file.File.data>`
        attribute using their HDF5 dataset name as key. Usually, however,
        data are accessed by their "given" name.

        This method returns a list of all "given" names of the datasets
        stored in :attr:`data <evefile.entities.file.File.data>`.

        Returns
        -------
        data : :class:`list`
            List of names of the data object(s) in :attr:`data`.

        """
        names = [item.metadata.name for key, item in self.data.items()]
        return names

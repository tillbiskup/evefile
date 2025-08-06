"""
.. include:: <isopub.txt>

*Mapping eveH5 contents to the data structures of the evefile package.*

.. sidebar:: Contents

    .. contents::
        :local:
        :depth: 2

There are different versions of the schema underlying the eveH5 files.
Hence, mapping the contents of an eveH5 file to the data model of the
evefile package requires to get the correct mapper for the specific
version. This is the typical use case for the factory pattern.

Users of the module hence will typically only obtain a
:obj:`VersionMapperFactory` object to get the correct mappers for individual
files. Furthermore, "users" basically boils down to the :class:`EveFile
<evefile.boundaries.evefile.EveFile>` class. Therefore, users of
the `evefile` package usually do not interact directly with any of the
classes provided by this module.


Overview
========

Being version agnostic with respect to eveH5 and SCML schema versions is a
central aspect of the evefile package. This requires facilities mapping
the actual eveH5 files to the data model provided by the entities
technical layer of the evefile subpackage. The :class:`File
<evefile.boundaries.evefile.File>` facade obtains
the correct :obj:`VersionMapper` object via the
:class:`VersionMapperFactory`, providing an :class:`HDF5File
<evefile.boundaries.eveh5.HDF5File>` resource object to the
factory. It is the duty of the factory to obtain the "version" attribute
from the :obj:`HDF5File <evefile.boundaries.eveh5.HDF5File>`
object (explicitly getting the attributes of the root group of the
:obj:`HDF5File <evefile.boundaries.eveh5.HDF5File>` object).


.. figure:: /uml/evefile.controllers.version_mapping.*
    :align: center

    Class hierarchy of the :mod:`evefile.controllers.version_mapping`
    module, providing the functionality to map different eveH5 file
    schemas to the data structure provided by the :class:`EveFile
    <evefile.boundaries.evefile.EveFile>` class. The factory
    will be used to get the correct mapper for a given eveH5 file.
    For each eveH5 schema version, there exists an individual
    ``VersionMapperVx`` class dealing with the version-specific mapping.
    The idea behind the ``Mapping`` class is to provide simple mappings for
    attributes and alike that need not be hard-coded and can be stored
    externally, *e.g.* in YAML files. This would make it easier to account
    for (simple) changes.


For each eveH5 schema version, there exists an individual
``VersionMapperVx`` class dealing with the version-specific mapping. That
part of the mapping common to all versions of the eveH5 schema takes place
in the :class:`VersionMapper` parent class, *e.g.* removing the chain. The
idea behind the ``Mapping`` class is to provide simple mappings for
attributes and alike that can be stored externally, *e.g.* in YAML files.
This would make it easier to account for (simple) changes.


Mapping tasks for eveH5 schema
==============================

What follows is a summary of the different aspects, for the time being
*not* divided for the different formats (up to v7):

* Map attributes of ``/`` and ``/c1`` to the file metadata. |cross|
* Convert monitor datasets from the ``device`` group to :obj:`MonitorData
  <evefile.entities.data.MonitorData>` objects. |cross|

  * We probably need to create subclasses for the different monitor
    datasets, at least distinguishing between numeric and non-numeric
    values.

* Map ``/c1/meta/PosCountTimer`` to :obj:`TimestampData
  <evefile.entities.data.TimestampData>` object. |cross|

* Starting with eveH5 v5: Map ``/LiveComment`` to :obj:`LogMessage
  <evefile.entities.file.LogMessage>` objects. |cross|

* Filter all datasets from the ``main`` section, with different goals:

  * Map array data to :obj:`ArrayChannelData
    <evefile.entities.data.ArrayChannelData>` objects (HDF5 groups
    having an attribute ``DeviceType`` set to ``Channel``). |cross|

    * Distinguish between MCA and scope data (at least). |cross|
    * Map additional datasets in main section (and snapshot). |cross|

  * Map all axis datasets to :obj:`AxisData
    <evefile.entities.data.AxisData>` objects. |cross|

    * How to distinguish between axes with and without encoders? |cross|
    * Read channels with RBV and replace axis values with RBV. |cross|

      * Most probably, the corresponding channel has the same *name*
        (not XML-ID, though!) as the axis, but with suffix ``_RBV``,
        and can thus be identified.
      * In case of axes with encoders, there may be additional datasets
        present, *e.g.*, those with suffix ``_Enc``.
      * In this case, instead of :obj:`NonencodedAxisData
        <evefile.entities.data.NonencodedAxisData>`,
        an :obj:`AxisData <evefile.entities.data.AxisData>`
        object needs to be created. (Currently, only :obj:`AxisData
        <evefile.entities.data.AxisData>` objects are created,
        what is a mistake as well...)

    * How to deal with pseudo-axes used as options in channel datasets? Do
      we need to deal with axes later? |cross|

  * Distinguish between single point and area data, and map area data to
    :obj:`AreaChannelData <evefile.entities.data.AreaChannelData>`
    objects. (|cross|)

    * Distinguish between scientific and sample cameras. |cross|
    * Which dataset is the "main" dataset for scientific cameras? |cross|

      * Starting with eve v1.39, it is ``TIFF1:chan1``, before, this is
        less clear, and there might not exist a dataset containing
        filenames with full paths, but only numbers.

    * Map sample camera datasets. |cross|

  * Map the additional data for average and interval channel data provided
    in the respective HDF5 groups to :obj:`AverageChannelData
    <evefile.entities.data.AverageChannelData>` and
    :obj:`IntervalChannelData
    <evefile.entities.data.IntervalChannelData>` objects,
    respectively. |cross|
  * Map normalized channel data (and the data provided in the
    respective HDF5 groups) to :obj:`NormalizedChannelData
    <evefile.entities.data.NormalizedChannelData>`. |cross|
  * Add all data objects to the :attr:`data
    <evefile.boundaries.evefile.EveFile.data>` attribute of the
    :obj:`EveFile <evefile.boundaries.evefile.EveFile>` object.
    (Has been done during mapping already.)

* Filter all datasets from the ``snapshot`` section, with different goals:

  * Map all HDF5 datasets that belong to one of the data objects in the
    :attr:`data <evefile.boundaries.evefile.EveFile.data>`
    attribute of the :obj:`EveFile
    <evefile.boundaries.evefile.EveFile>` object to their respective
    attributes.
  * Map all HDF5 datasets remaining (if any) to data objects
    corresponding to their respective data type.
  * Add all data objects to the :attr:`snapshots
    <evefile.boundaries.evefile.EveFile.snapshots>` attribute of the
    :obj:`EveFile  <evefile.boundaries.evefile.EveFile>` object.
    |cross|


Most probably, not all these tasks can be inferred from the contents of an
eveH5 file alone. In this case, additional mapping tables, eventually
perhaps even on a per-measurement-station level, are necessary.


.. admonition:: Questions to address

    * How were the log messages/live comments saved before v5?

    * How to deal with options that are monitored? Check whether they change
      for a given channel/axis and if so, expand them (“fill”) for each
      PosCount of the corresponding channel/axis, and otherwise set as
      scalar attribute?

    * How to deal with the situation that not all actual data read from eveH5
      are numeric. Of course, non-numeric data cannot be plotted. But how
      to distinguish sensibly?

      * The :mod:`evefile.entities.data` module provides some
        distinct classes for this, at least for now
        :class:`NonnumericChannelData
        <evefile.entities.data.NonnumericChannelData>`.


Module documentation
====================

"""

import logging
import sys

from evefile import entities

logger = logging.getLogger(__name__)


class VersionMapperFactory:
    """
    Factory for obtaining the correct version mapper object.

    There are different versions of the schema underlying the eveH5 files.
    Hence, mapping the contents of an eveH5 file to the data model of the
    evedata package requires to get the correct mapper for the specific
    version. This is the typical use case for the factory pattern.


    Attributes
    ----------
    eveh5 : :class:`evedata.evefile.boundaries.eveh5.HDF5File`
        Python object representation of an eveH5 file

    Raises
    ------
    ValueError
        Raised if no eveh5 object is present


    Examples
    --------
    Using the factory is pretty simple. There are actually two ways how to
    set the eveh5 attribute -- either explicitly or when calling the
    :meth:`get_mapper` method of the factory:

    .. code-block::

        factory = VersionMapperFactory()
        factory.eveh5 = eveh5_object
        mapper = factory.get_mapper()

    .. code-block::

        factory = VersionMapperFactory()
        mapper = factory.get_mapper(eveh5=eveh5_object)

    In both cases, ``mapper`` will contain the correct mapper object,
    and ``eveh5_object`` contains the Python object representation of an
    eveH5 file.

    """

    def __init__(self):
        self.eveh5 = None

    def get_mapper(self, eveh5=None):
        """
        Return the correct mapper for a given eveH5 file.

        For convenience, the returned mapper has its
        :attr:`VersionMapper.source` attribute already set to the
        ``eveh5`` object used to get the mapper for.

        Parameters
        ----------
        eveh5 : :class:`evedata.evefile.boundaries.eveh5.HDF5File`
            Python object representation of an eveH5 file

        Returns
        -------
        mapper : :class:`VersionMapper`
            Mapper used to map the eveH5 file contents to evedata structures.

        Raises
        ------
        ValueError
            Raised if no eveh5 object is present

        AttributeError
            Raised if no matching :class:`VersionMapper` class can be found

        """
        if eveh5:
            self.eveh5 = eveh5
        if not self.eveh5:
            raise ValueError("Missing eveh5 object")
        version = self.eveh5.attributes["EVEH5Version"].split(".")[0]
        try:
            mapper = getattr(
                sys.modules[__name__], f"VersionMapperV{version}"
            )()
        except AttributeError as exc:
            message = f"No mapper for version {version}"
            logger.error(message)
            raise AttributeError(message) from exc
        mapper.source = self.eveh5
        return mapper


class VersionMapper:
    """
    Mapper for mapping the eveH5 file contents to evedata structures.

    This is the base class for all version-dependent mappers. Given that
    there are different versions of the eveH5 schema, each version gets
    handled by a distinct mapper subclass.

    To get an object of the appropriate class, use the
    :class:`VersionMapperFactory` factory.


    Attributes
    ----------
    source : :class:`evedata.evefile.boundaries.eveh5.HDF5File`
        Python object representation of an eveH5 file

    destination : :class:`evedata.evefile.boundaries.evefile.EveFile`
        High(er)-level evedata structure representing an eveH5 file

    datasets2map_in_main : :class:`list`
        Names of the datasets in the main section not yet mapped.

        In order to not have to check all datasets several times,
        this list contains only those datasets not yet mapped. Hence,
        every private mapping method removes those names from the list it
        handled successfully.

    datasets2map_in_snapshot : :class:`list`
        Names of the datasets in the snapshot section not yet mapped.

        In order to not have to check all datasets several times,
        this list contains only those datasets not yet mapped. Hence,
        every private mapping method removes those names from the list it
        handled successfully.

    datasets2map_in_monitor : :class:`list`
        Names of the datasets in the monitor section not yet mapped.

        Note that the monitor section is usually termed "device".

        In order to not have to check all datasets several times,
        this list contains only those datasets not yet mapped. Hence,
        every private mapping method removes those names from the list it
        handled successfully.

    Raises
    ------
    ValueError
        Raised if either source or destination are not provided


    Examples
    --------
    Although the :class:`VersionMapper` class is *not* meant to be used
    directly, its use is prototypical for all the concrete mappers:

    .. code-block::

        mapper = VersionMapper()
        mapper.map(source=eveh5, destination=evefile)

    Usually, you will obtain the correct mapper from the
    :class:`VersionMapperFactory`. In this case, the returned mapper has
    its :attr:`source` attribute already set for convenience:

    .. code-block::

        factory = VersionMapperFactory()
        mapper = factory.get_mapper(eveh5=eveh5)
        mapper.map(destination=evefile)


    """

    def __init__(self):
        self.source = None
        self.destination = None
        self.datasets2map_in_main = []
        self.datasets2map_in_snapshot = []
        self.datasets2map_in_monitor = []
        self._main_group = None
        self._snapshot_group = None
        self._monitor_group = None

    def map(self, source=None, destination=None):
        """
        Map the eveH5 file contents to evedata structures.

        Parameters
        ----------
        source : :class:`evedata.evefile.boundaries.eveh5.HDF5File`
            Python object representation of an eveH5 file

        destination : :class:`evedata.evefile.boundaries.evefile.EveFile`
            High(er)-level evedata structure representing an eveH5 file

        Raises
        ------
        ValueError
            Raised if either source or destination are not provided

        """
        if source:
            self.source = source
        if destination:
            self.destination = destination
        self._check_prerequisites()
        self._set_dataset_names()
        self._map()

    @staticmethod
    def get_hdf5_dataset_importer(dataset=None, mapping=None):
        """
        Get an importer object for HDF5 datasets with properties set.

        Data are loaded on demand, not already when initially loading the
        eveH5 file. Hence, the need for a mechanism to provide the relevant
        information where to get the relevant data from and how. Different
        versions of the underlying eveH5 schema differ even in whether all
        data belonging to one :obj:`Data` object are located in one HDF5
        dataset or spread over multiple HDF5 datasets. In the latter case,
        individual importers are necessary for the separate HDF5 datasets.

        As the :class:`VersionMapper` class deals with each HDF5 dataset
        individually, some fundamental settings for the
        :class:`HDF5DataImporter
        <evedata.evefile.entities.data.HDF5DataImporter>` are readily
        available. Additionally, the ``mapping`` parameter provides the
        information necessary to create the correct information in the
        :attr:`HDF5DataImporter.mapping
        <evedata.evefile.entities.data.HDF5DataImporter.mapping>` attribute.

        .. important::
            The keys in the dictionary provided via the ``mapping``
            parameter are **integers, not strings**, as usual for
            dictionaries. This allows to directly use the keys for
            indexing the tuple returned by ``numpy.dtype.names``. To be
            explicit, here is an example:

            .. code-block::

                dataset = HDF5Dataset()
                importer_mapping = {
                    0: "milliseconds",
                    1: "data",
                }
                importer = self.get_hdf5_dataset_importer(
                    dataset=dataset, mapping=importer_mapping
                )

            Of course, in reality you will not just instantiate an empty
            :obj:`HDF5Dataset <evedata.evefile.boundaries.eveh5.HDF5Dataset>`
            object, but have one available within your mapper.


        Parameters
        ----------
        dataset : :class:`evedata.evefile.boundaries.eveh5.HDF5Dataset`
            Representation of an HDF5 dataset.

        mapping : :class:`dict`
            Table mapping HDF5 dataset columns to data class attributes.

            **Note**: The keys in this dictionary are *integers*,
            not strings, as usual for dictionaries. This allows to directly
            use the keys for indexing the tuple returned by
            ``numpy.dtype.names``.

        Returns
        -------
        importer : :class:`evedata.evefile.entities.data.HDF5DataImporter`
            HDF5 dataset importer

        """
        if mapping is None:
            mapping = {}
        importer = entities.data.HDF5DataImporter()
        importer.source = dataset.filename
        importer.item = dataset.name
        for key, value in mapping.items():
            importer.mapping[dataset.dtype.names[key]] = value
        return importer

    def _check_prerequisites(self):
        if not self.source:
            raise ValueError("Missing source to map from.")
        if not self.destination:
            raise ValueError("Missing destination to map to.")

    def _set_dataset_names(self):
        pass

    def _map(self):
        pass


class VersionMapperV7(VersionMapper):
    """
    Mapper for mapping eveH5 v7 file contents to evedata structures.

    The only difference to the previous version v6: the attribute
    ``Simulation`` has beem added on the file root level and is mapped
    as a Boolean value onto the :attr:`File.metadata.simulation
    <evedata.evefile.entities.file.Metadata.simulation>` attribute.

    Attributes
    ----------
    source : :class:`evedata.evefile.boundaries.eveh5.HDF5File`
        Python object representation of an eveH5 file

    destination : :class:`evedata.evefile.boundaries.evefile.File`
        High(er)-level evedata structure representing an eveH5 file

    Raises
    ------
    ValueError
        Raised if either source or destination are not provided


    Examples
    --------
    Mapping a given eveH5 file to the evedata structures is the same for
    each of the mappers:

    .. code-block::

        mapper = VersionMapperV7()
        mapper.map(source=eveh5, destination=evefile)

    Usually, you will obtain the correct mapper from the
    :class:`VersionMapperFactory`. In this case, the returned mapper has
    its :attr:`source` attribute already set for convenience:

    .. code-block::

        factory = VersionMapperFactory()
        mapper = factory.get_mapper(eveh5=eveh5)
        mapper.map(destination=evefile)

    """

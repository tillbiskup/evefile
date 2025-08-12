"""

*Entities representing an eveH5 file on the data level.*

.. sidebar:: Contents

    .. contents::
        :local:
        :depth: 2

Data are organised in "datasets" within HDF5, and the
:mod:`evefile.entities.data` module provides the relevant entities
to describe these datasets. Although currently (as of 07/2024, eve version
2.1) neither average nor interval detector channels save the individual
data points, at least the former is a clear need of the
engineers/scientists. Hence, the data model already respects this use
case. As per position (count) there can be a variable number of measured
points, the resulting array is no longer rectangular, but a "ragged
array". While storing such arrays is possible directly in HDF5,
the implementation within evefile is entirely independent of the actual
representation in the eveH5 file.


Overview
========

A first overview of the classes implemented in this module and their
hierarchy is given in the UML diagram below, :numref:`Fig. %s
<fig-uml_evefile.data_api>`. The first distinction is made
between :class:`MonitorData` and :class:`MeasureData`, with the former
having timestamps (in milliseconds) as their quantisation axis, and the
latter individual positions (integer values). :class:`MeasureData` can
further be separated into :class:`AxisData`, :class:`ChannelData`,
and :class:`DeviceData`. The :class:`TimestampData` class is somewhat
special, as it (only) gets used to map timestamps to positions and does
not correspond to any physical device or option of such device. Generally,
each data class comes with its corresponding metadata class implemented in
the :mod:`evefile.entities.metadata` module.


.. _fig-uml_evefile.data_api:

.. figure:: /uml/evefile.entities.data.*
    :align: center
    :width: 750px

    Class hierarchy of the :mod:`evefile.entities.data` module.
    Each class has a corresponding metadata class in the
    :mod:`evefile.entities.metadata` module. While in this
    diagram, some child classes seem to be identical, they have a
    different type of metadata (see the
    :mod:`evefile.entities.metadata` module). Generally, having
    different types serves to discriminate where necessary between
    detector channels and motor axes.
    You may click on the image for a larger view.




Individual classes
------------------

The following is not a strict inheritance hierarchy, but rather a grouped
hierarchical list of classes for quick access to their individual API
documentation:

* :class:`Data`

  * :class:`MonitorData`
  * :class:`MeasureData`

    * :class:`DeviceData`
    * :class:`TimestampData`
    * :class:`AxisData`
    * :class:`ChannelData`

      * :class:`SinglePointChannelData`

        * :class:`SinglePointNormalizedChannelData`

      * :class:`AverageChannelData`

        * :class:`AverageNormalizedChannelData`

      * :class:`IntervalChannelData`

        * :class:`IntervalNormalizedChannelData`



Special aspects
===============

There is a number of special aspects that need to be taken into account
when reading data. These are detailed below.


Sorting non-monotonic positions
-------------------------------

For :class:`MeasureData`, positions ("PosCounts") need not be
monotonically increasing. This is due to the way the engine handles the
different scan modules and writes data. However, this will usually be a
problem for the analysis. Therefore, positions need to be sorted
monotonically, and this is done during data import.


Handling duplicate positions
----------------------------

Although technically speaking a bug, some (older) measurement files
contain duplicate positions ("PosCounts"). Here, the handling is different
for :class:`AxisData` and :class:`ChannelData`, but in both cases taken
care of during data import:

* For :class:`AxisData`, only the *last* position is taken.
* For :class:`ChannelData`, only the *first* position is taken.


Module documentation
====================

"""

import copy
import logging

import h5py
import numpy as np

from evefile.entities import metadata

logger = logging.getLogger(__name__)


class Data:
    """
    Data recorded from the devices involved in a measurement.

    This is the base class for all data(sets) and not meant to be used
    directly. Rather, one of the individual subclasses should actually be
    used.

    When subclassing, make sure to create the corresponding metadata class
    in the :mod:`evefile.entities.metadata` module as well.

    Data are read from HDF5 files, and to save time and resources, actual
    data are only read upon request.

    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.Metadata`
        Relevant metadata for the individual device.

    options : :class:`dict`
        (Variable) options of the device.

        Devices can have options. Generally, there are two types of
        options: those whose values are *not* changing within a given scan
        module, and those whose values can potentially change for every
        individual position (count). The latter are stored here as
        key--value pairs with the key corresponding to the option name.
        The former are stored in the
        :attr:`evefile.entities.metadata.Metadata.options` attribute.

    importer : :class:`list`
        Importer objects for the data and possibly (variable) options.

        Each item is a :obj:`DataImporter` object.

        Data are loaded on demand, not already when initially loading the
        eveH5 file. Hence, the need for a mechanism to provide the relevant
        information where to get the relevant data from and how. Different
        versions of the underlying eveH5 schema differ even in whether all
        data belonging to one :obj:`Data` object are located in one HDF5
        dataset or spread over multiple HDF5 datasets. In the latter case,
        individual importers are necessary for the separate HDF5 datasets.
        Hence, the list of importers.

    Examples
    --------
    The :class:`Data` class is not meant to be used directly, as any
    entities, but rather indirectly by means of the respective facades in
    the boundaries technical layer of the ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.Metadata()
        self.options = {}
        self.importer = []
        self._data = None

    def __str__(self):
        """
        Human-readable representation of the class/object.

        Returns
        -------
        output : :class:`str`
            String containing name and class name

        """
        return f"{self.metadata.name} <{type(self).__name__}>"

    @property
    def data(self):
        """
        Actual data recorded from the device.

        Data are loaded only on demand. Hence, upon the first access of the
        :attr:`data` property, the :meth:`get_data` method will be called,
        calling out to the respective importers.

        Returns
        -------
        data : :class:`numpy.ndarray`
            Actual data recorded from the device.

            The actual data type (:class:`numpy.dtype`) depends on the
            specific dataset loaded.

        """
        if self._data is None:
            self.get_data()
        return self._data

    @data.setter
    def data(self, data=None):
        self._data = data

    def get_data(self):
        """
        Load data (and variable option data) using the respective importer.

        Data are loaded only on demand. Hence, upon the first access of the
        :attr:`data` property, this method will be called, calling out to
        the respective importers.

        As :obj:`Data` objects may contain (variable) options that are
        themselves data, but loading these data is only triggered when
        accessing the :attr:`data` property, you can either once access the
        :attr:`data` property or call this method.

        Data may be spread over several HDF5 datasets, depending on the
        version of the eveH5 file read. Hence, there may be several
        importers, and they are dealt with sequentially.

        Furthermore, for each importer type, there is a special private
        method ``_import_from_<importer-type>``, with ``<importer-type>``
        being the lowercase class name. Those classes using additional
        importers beyond :class:`HDF5DataImporter` need to implement
        additional private methods to handle the special importer classes. A
        typical use case is the :class:`AreaChannelData` class dealing with
        image data stored mostly in separate files.

        """
        for importer in self.importer:
            self._import_from_hdf5dataimporter(importer=importer)

    def _import_from_hdf5dataimporter(self, importer=None):
        importer.load()
        for column_name, attribute in importer.mapping.items():
            setattr(self, attribute, importer.data[column_name])

    def copy_attributes_from(self, source=None):
        """
        Obtain attributes from another :obj:`Data` object.

        Sometimes, it is useful to obtain the (public) attributes from
        another :obj:`Data` object. Note that only public attributes are
        copied. Furthermore, a (true) copy of the attributes is obtained,
        hence the properties of source and target are actually different
        objects.

        Parameters
        ----------
        source : :class:`Data`
            Object to copy attributes from.

            Should typically be of the same (super)type.

        Raises
        ------
        ValueError
            Raised if no source is provided to copy attributes from.

        """
        if not source:
            raise ValueError("No source provided to copy attributes from.")
        public_attributes = [
            item
            for item in self.__dict__
            if not (item.startswith("_") or item == "metadata")
        ]
        for attribute in public_attributes:
            try:
                setattr(
                    self, attribute, copy.copy(getattr(source, attribute))
                )
            except AttributeError:
                logger.debug(
                    "Cannot set non-existing attribute %s", attribute
                )
        self.metadata.copy_attributes_from(source.metadata)


class MonitorData(Data):
    """
    Data from devices monitored, but not controlled by the eve engine.

    In contrast to :class:`MeasureData`, :class:`MonitorData` do not have
    a position as primary axis, but a timestamp in milliseconds, *i.e.*,
    the :attr:`milliseconds` attribute.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.MonitorMetadata`
        Relevant metadata for the individual device.

    milliseconds : :class:`numpy.ndarray`
        Time in milliseconds since start of the scan.


    Examples
    --------
    The :class:`MonitorData` class is not meant to be used directly, as any
    entities, but rather indirectly by means of the respective facades in
    the boundaries technical layer of the ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.MonitorMetadata()
        self.milliseconds = np.ndarray(shape=[], dtype=int)

    def __str__(self):
        """
        Human-readable representation of the class/object.

        Returns
        -------
        output : :class:`str`
            String containing name and class name

        """
        return (
            f"{self.metadata.name} ({self.metadata.id}) "
            f"<{type(self).__name__}>"
        )


class MeasureData(Data):
    """
    Base class for data from devices actually controlled by the eve engine.

    In contrast to :class:`MonitorData`, :class:`MeasureData` have a
    position as primary axis rather than a timestamp in milliseconds, *i.e.*,
    the :attr:`positions` attribute.

    .. note::

        Positions and (all) corresponding data are sorted upon load. For
        the handling of duplicate positions in :class:`AxisData` and
        :class:`ChannelData`. see there.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.MeasureMetadata`
        Relevant metadata for the individual device.


    Examples
    --------
    The :class:`MeasureData` class is not meant to be used directly, as any
    entities, but rather indirectly by means of the respective facades in
    the boundaries technical layer of the ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.MeasureMetadata()
        self._position_counts = None

    def __str__(self):
        """
        Human-readable representation of the class/object.

        Returns
        -------
        output : :class:`str`
            String containing name and class name

        """
        return (
            f"{self.metadata.name} ({self.metadata.id}) "
            f"<{type(self).__name__}>"
        )

    @property
    def position_counts(self):
        """
        Position counts data are recorded for.

        Each data "point" corresponds to an overall position of all
        actuators (motor axes) of the setup and is assigned an individual
        "position count" (an integer number).

        Actual data recorded from the device.

        Data are loaded only on demand. Hence, upon the first access of the
        :attr:`positions` property, the :meth:`get_data` method will be
        called, calling out to the respective importers.

        Returns
        -------
        positions : :class:`numpy.ndarray`
            Position values data are recorded for.

            The actual data type (:class:`numpy.dtype`) is usually int.

        """
        if self._position_counts is None:
            self.get_data()
        return self._position_counts

    @position_counts.setter
    def position_counts(self, positions=None):
        self._position_counts = positions

    def _import_from_hdf5dataimporter(self, importer=None):
        """
        Import data from HDF5 using data importer.

        .. note::

            The only difference to the superclass method is the sorting of
            the arrays by positions, as due to the way values are recorded,
            eveH5 files can have positions in non-ascending order.

        Parameters
        ----------
        importer : :class:`HDF5DataImporter`
            Importer used to import the data

        """
        super()._import_from_hdf5dataimporter(importer=importer)
        sort_indices = np.argsort(self.position_counts)
        for attribute in importer.mapping.values():
            setattr(self, attribute, getattr(self, attribute)[sort_indices])


class DeviceData(MeasureData):
    """
    Data from (dumb) devices.

    Three types of devices are distinguished by the eve measurement
    program: (dumb) devices, motor axes, and detector channels.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.DeviceMetadata`
        Relevant metadata for the individual device.


    Examples
    --------
    The :class:`DeviceData` class is not meant to be used directly, as any
    entities, but rather indirectly by means of the respective facades in
    the boundaries technical layer of the ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.DeviceMetadata()


class AxisData(MeasureData):
    """
    Data from motor axes.

    Three types of devices are distinguished by the eve measurement
    program: (dumb) devices, motor axes, and detector channels.

    .. note::

        Positions and (all) corresponding data are sorted upon load. In
        case of duplicate positions, only the *last* position is retained.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.AxisMetadata`
        Relevant metadata for the individual device.

    set_values : None
        Values the axis should have been set to.

        While the :attr:`Data.data` attribute contains the actual
        positions of the axis, here, the originally intended positions are
        stored. This allows for easily checking whether the axis has been
        positioned within a scan as intended.


    Examples
    --------
    The :class:`AxisData` class is not meant to be used directly, as any
    entities, but rather indirectly by means of the respective facades in
    the boundaries technical layer of the ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.AxisMetadata()
        self.set_values = None

    def _import_from_hdf5dataimporter(self, importer=None):
        """
        Import data from HDF5 using data importer.

        .. note::

            The only difference to the superclass method is its handling of
            duplicate position values: in this case, only the *last* position
            is taken.

        Parameters
        ----------
        importer : :class:`HDF5DataImporter`
            Importer used to import the data

        """
        super()._import_from_hdf5dataimporter(importer=importer)
        indices = np.where(
            np.diff([*self.position_counts, self.position_counts[-1] + 1])
        )
        for attribute in importer.mapping.values():
            setattr(self, attribute, getattr(self, attribute)[indices])


class ChannelData(MeasureData):
    """
    Data from detector channels.

    Three types of devices are distinguished by the eve measurement
    program: (dumb) devices, motor axes, and detector channels.

    .. note::

        Positions and (all) corresponding data are sorted upon load. In
        case of duplicate positions, only the *first* position is retained.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.ChannelMetadata`
        Relevant metadata for the individual device.


    Examples
    --------
    The :class:`ChannelData` class is not meant to be used directly, as any
    entities, but rather indirectly by means of the respective facades in
    the boundaries technical layer of the ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.ChannelMetadata()

    def _import_from_hdf5dataimporter(self, importer=None):
        """
        Import data from HDF5 using data importer.

        .. note::

            The only difference to the superclass method is its handling of
            duplicate position values: in this case, only the *first*
            position is taken.

        Parameters
        ----------
        importer : :class:`HDF5DataImporter`
            Importer used to import the data

        """
        super()._import_from_hdf5dataimporter(importer=importer)
        indices = (
            np.where(
                ((self.position_counts[:-1] - self.position_counts[1:]) + 1)
                > 0
            )[0]
            + 1
        )
        for attribute in importer.mapping.values():
            setattr(
                self, attribute, np.delete(getattr(self, attribute), indices)
            )


class TimestampData(MeasureData):
    """
    Data correlating the positions to the time used for monitors.

    There are generally two different types of devices: those directly
    controlled by the eve engine, and those who are monitored. The former
    are instances of the :class:`MeasureData` class, the latter of the
    :class:`MonitorData` class.

    The :class:`TimestampData` class allows to map the time stamps (in
    milliseconds) of the :class:`MonitorData` data to positions of
    :class:`MeasureData` data. This is a necessary prerequisite to
    correlate monitored values to the data from controlled devices,
    such as motor axes and detector channels.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.TimestampMetadata`
        Relevant metadata for the individual device.


    Examples
    --------
    The :class:`TimestampData` class is not meant to be used directly, as any
    entities, but rather indirectly by means of the respective facades in
    the boundaries technical layer of the ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.TimestampMetadata()

    def get_position(self, time=-1):
        """
        Get position for a given (list of) time(stamp)s.

        This method is used to map monitor timestamps to positions.

        .. note::

            Due to not being able to distinguish between axes and channels
            up to eveH5 v7, timestamps are generally mapped to the
            *previous* position.


        Parameters
        ----------
        time : :class:`int` | :class:`list` | :class:`numpy.ndarray`
            Time(s) a position is requested for.

        Returns
        -------
        positions : :class:`numpy.ndarray`
            Position(s) corresponding to the timestamp(s) given.

        """
        time = np.asarray(time)
        time = np.where(time < 0, self.data[0], time)
        idx = np.digitize(time, self.data)
        return self.position_counts[idx - 1]


class SinglePointChannelData(ChannelData):
    """
    Data for channels with numeric 0D data.

    Detector channels can be distinguished by the dimension of their data:

    0D
        scalar values per position, including average and interval channels
    1D
        array values, *i.e.* vectors, per position
    2D
        area values, *i.e.* images, per position

    This class represents 0D, scalar values.

    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.SinglePointChannelMetadata`
        Relevant metadata for the individual device.


    Examples
    --------
    The :class:`SinglePointChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.SinglePointChannelMetadata()


class AverageChannelData(ChannelData):
    """
    Data for channels with averaged numeric 0D data.

    Detector channels can be distinguished by the dimension of their data:

    0D
        scalar values per position, including average and interval channels
    1D
        array values, *i.e.* vectors, per position
    2D
        area values, *i.e.* images, per position

    This class represents 0D, scalar values that are averaged.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.AverageChannelMetadata`
        Relevant metadata for the individual device.

    raw_data : Any
        The raw individual values measured.

    attempts : numpy.ndarray
        Short description


    Examples
    --------
    The :class:`AverageChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.AverageChannelMetadata()
        self.raw_data = None
        self.attempts = np.ndarray(shape=[], dtype=int)
        self._mean = None
        self._std = None

    @property
    def mean(self):
        """
        Mean values for channel data.

        Returns
        -------
        mean : :class:`numpy.ndarray`
            The mean of the values recorded.

            If more values have been recorded than should be averaged
            over, only the number of values to average over are taken from
            the end of the individual :attr:`raw_data` row.

        """
        if self._mean is None:
            if self.raw_data is not None:
                self._mean = self.raw_data.mean(axis=1)
            else:
                self._mean = self.data
        return self._mean

    @property
    def std(self):
        """
        Standard deviation values for channel data.

        Returns
        -------
        mean : :class:`numpy.ndarray`
            The standard deviation of the values recorded.

            If more values have been recorded than should be averaged
            over, only the number of values to average over are taken from
            the end of the individual :attr:`raw_data` row to calculate
            the standard deviation.

        """
        if self._std is None and self.raw_data is not None:
            self._std = self.raw_data.std(axis=1)
        return self._std

    @std.setter
    def std(self, std=None):
        self._std = std


class IntervalChannelData(ChannelData):
    """
    Data for channels with numeric 0D data measured in a time interval.

    Detector channels can be distinguished by the dimension of their data:

    0D
        scalar values per position, including average and interval channels
    1D
        array values, *i.e.* vectors, per position
    2D
        area values, *i.e.* images, per position

    This class represents 0D, scalar values that are measured in a time
    interval.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.IntervalChannelMetadata`
        Relevant metadata for the individual device.

    raw_data : Any
        The raw individual values measured in the given time interval.

    counts : numpy.ndarray
        The number of values measured in the given time interval.

        Note that this value may change for each individual position.


    Examples
    --------
    The :class:`IntervalChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.IntervalChannelMetadata()
        self.raw_data = None
        self.counts = np.ndarray(shape=[], dtype=int)
        self._mean = None
        self._std = None

    @property
    def mean(self):
        """
        Mean values for channel data.

        Returns
        -------
        mean : :class:`numpy.ndarray`
            The mean of the values measured in the given time interval.

        """
        if self._mean is None:
            if self.raw_data is not None:
                self._mean = self.raw_data.mean(axis=1)
            else:
                self._mean = self.data
        return self._mean

    @property
    def std(self):
        """
        Standard deviation values for channel data.

        Returns
        -------
        mean : :class:`numpy.ndarray`
            The standard deviation of the values measured in the given
            time interval.

        """
        if self._std is None and self.raw_data is not None:
            self._std = self.raw_data.std(axis=1)
        return self._std

    @std.setter
    def std(self, std=None):
        self._std = std


class NormalizedChannelData:
    """
    Mixin class (interface) for normalized channel data.

    0D channels can be normalized by the data of another 0D channel,
    *i.e.* by dividing its values by the values of the normalizing channel.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.AreaChannelMetadata`
        Relevant metadata for normalization.

    normalized_data : Any
        Data that have been normalized.

        Normalization takes place by dividing by the values of the
        normalizing channel.

    normalizing_data : Any
        Data used for normalization.

    Raises
    ------
    exception
        Short description when and why raised


    Examples
    --------
    The :class:`AreaChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.NormalizedChannelMetadata()
        self.normalized_data = None
        self.normalizing_data = None


class SinglePointNormalizedChannelData(
    SinglePointChannelData, NormalizedChannelData
):
    """
    Data for channels with normalized numeric 0D data.

    Detector channels can be distinguished by the dimension of their data:

    0D
        scalar values per position, including average and interval channels
    1D
        array values, *i.e.* vectors, per position
    2D
        area values, *i.e.* images, per position

    This class represents 0D, scalar values that are normalized by the
    data of another 0D channel.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.SinglePointNormalizedChannelMetadata`
        Relevant metadata for the individual normalized device.


    Examples
    --------
    The :class:`SinglePointNormalizedChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.SinglePointNormalizedChannelMetadata()


class AverageNormalizedChannelData(AverageChannelData, NormalizedChannelData):
    """
    Data for channels with normalized averaged numeric 0D data.

    Detector channels can be distinguished by the dimension of their data:

    0D
        scalar values per position, including average and interval channels
    1D
        array values, *i.e.* vectors, per position
    2D
        area values, *i.e.* images, per position

    This class represents 0D, scalar values that are averaged and
    normalized by the data of another 0D channel.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.AverageNormalizedChannelMetadata`
        Relevant metadata for the individual normalized device.


    Examples
    --------
    The :class:`AverageNormalizedChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.AverageNormalizedChannelMetadata()


class IntervalNormalizedChannelData(
    IntervalChannelData, NormalizedChannelData
):
    """
    Data for channels with normalized interval-measured numeric 0D data.

    Detector channels can be distinguished by the dimension of their data:

    0D
        scalar values per position, including average and interval channels
    1D
        array values, *i.e.* vectors, per position
    2D
        area values, *i.e.* images, per position

    This class represents 0D, scalar values that are measured in a time
    interval and normalized by the data of another 0D channel.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.IntervalNormalizedChannelMetadata`
        Relevant metadata for the individual normalized device.

    Examples
    --------
    The :class:`IntervalNormalizedChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.IntervalNormalizedChannelMetadata()


class DataImporter:
    """
    Base class for data importer.

    Data need to be imported from somewhere. And usually, data should only
    be imported once they are requested, to save time and resources.

    Actual importer classes inherit from this base class and implement the
    private method :meth:`_load`. This method simply returns the loaded data.

    Optionally, preprocessing will be applied to the data loaded, if the
    list :attr:`preprocessing` is not empty.


    Attributes
    ----------
    source : :class:`str`
        Source the data should be loaded from.

        Typically, a file name.

    preprocessing : :class:`list`
        Preprocessing steps applied after loading the original data.

        Each entry in the list is an object of type
        :class:`ImporterPreprocessingStep`.

    Raises
    ------
    ValueError
        Raised upon load if no source is provided.


    Examples
    --------
    While this base class is not intended to be used directly, the general
    usage is the same for all descendants:

    .. code-block::

        importer = DataImporter()
        data = importer.import(source="myfilename")

    For convenience, you can set the source when instantiating the object.
    This makes actually importing simpler, not having to worry anymore
    about the source:

    .. code-block::

        importer = DataImporter(source="myfilename")
        data = importer.import()

    """

    def __init__(self, source=""):
        self.source = source
        self.preprocessing = []

    def load(self, source=""):
        """
        Load data from source.

        The method first checks for the source to be present, and afterwards
        calls out to the private method :meth:`_load` that does the actual
        business. Child classes hence need to implement this private method.
        Make sure to return the loaded data from this method.

        Once loaded, the data are preprocessed with each of the
        preprocessing steps defined in :attr:`preprocessing`.

        Parameters
        ----------
        source : :class:`str`
            Source the data should be loaded from.

            Typically, a file name.

        Raises
        ------
        ValueError
            Raised if no source is provided.

        Returns
        -------
        data : any
            Data loaded from the source.

            The actual type of data depends on the source and importer type.

        """
        if source:
            self.source = source
        if not self.source:
            raise ValueError("No source provided to load data from.")
        raw_data = self._load()  # noqa
        for task in self.preprocessing:
            raw_data = task.process(raw_data)
        return raw_data

    def _load(self):
        pass


class HDF5DataImporter(DataImporter):
    """
    Load data from HDF5 dataset.

    HDF5 files are organised hierarchically, with groups as nodes and
    datasets as leafs. Data can (only) be contained in datasets, and this is
    what this importer is concerned about.

    .. note::
        Perhaps it is possible to move this class to the boundary technical
        layer, by means of creating an (abstract) DataImporterFactory in the
        entities layer and a concrete factory in the boundary layer. The
        only complication currently: the controller technical layer needs to
        access the concrete DataImporterFactory.


    Attributes
    ----------
    source : :class:`str`
        Source the data should be loaded from.

        Name of an HDF5 file.

    item : :class:`str`
        The dataset within the HDF5 file.

        Datasets are addressed by a path-like string, with slashes
        separating the hierarchy levels in the file.

    mapping : :class:`dict`
        Mapping table for table columns to :obj:`Data` object attributes.

        HDF5 datasets in eveH5 files usually consist of at least two columns
        for their data, the first either the position or the time since
        start of the measurement in milliseconds. Besides this, there can be
        more than one additional column for the actual data. As the
        structure of the datasets changed and will change, there is a need
        for a mapping table that gets filled properly by the
        :class:`VersionMapper
        <evefile.controllers.version_mapping.VersionMapper>` class.

        Furthermore, storing this mapping information is relevant as data
        are usually only loaded upon request, not preliminary, to save time
        and resources.

    data : :class:`numpy.ndarray`
        Data loaded from the HDF5 dataset.

        The actual data type (:class:`numpy.dtype`) depends on the
        specific dataset loaded.

    Raises
    ------
    ValueError
        Raised upon load if either source or item are not provided.


    Examples
    --------
    To import data from an HDF5 dataset located in an HDF5 file, you need to
    provide both, file name (source) and dataset name (item):

    .. code-block::

        importer = HDF5DataImporter()
        importer.source = "test.h5"
        importer.item = "/c1/main/test"
        data = importer.load()

    You can, for convenience, provide both, source and item upon
    instantiating the importer object:

    .. code-block::

        importer = HDF5DataImporter(source="test.h5", item="/c1/main/test")
        data = importer.load()

    """

    def __init__(self, source=""):
        super().__init__(source=source)
        self.item = ""
        self.mapping = {}
        self.data = None

    def load(self, source="", item=""):
        """
        Load data from source.

        The method first checks for the source to be present, and afterwards
        calls out to the private method :meth:`_load` that does the actual
        business. Child classes hence need to implement this private method.
        Make sure to return the loaded data from this method.

        Besides returning the data (for convenience), they are set to the
        :attr:`data` attribute for later access.

        Parameters
        ----------
        source : :class:`str`
            Source the data should be loaded from.

            Name of an HDF5 file.

        item : :class:`str`
            The dataset within the HDF5 file.

            Datasets are addressed by a path-like string, with slashes
            separating the hierarchy levels in the file.

        Raises
        ------
        ValueError
            Raised if either source or item are not provided.

        Returns
        -------
        data : :class:`numpy.ndarray`
            Data loaded from the HDF5 dataset.

            The actual data type (:class:`numpy.dtype`) depends on the
            specific dataset loaded.

        """
        if item:
            self.item = item
        if not self.item:
            raise ValueError("No item to load data from.")
        self.data = super().load(source=source)
        return self.data

    def _load(self):
        with h5py.File(self.source, "r") as file:
            self.data = file[self.item][...]
        return self.data

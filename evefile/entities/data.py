"""

*Entities representing an eveH5 file on the data level.*

.. sidebar:: Contents

    .. contents::
        :local:
        :depth: 2

Data are organised in "datasets" within HDF5, and the
:mod:`evefile.entities.data` module provides the relevant entities
to describe these datasets.

Please note that in contrast to the `evedata
<https://evedata.docs.radiometry.de/>`_ package, the ``evefile`` package has
a somewhat reduced data model, *e.g.* not considering individual data points
for average and interval channels (that are currently not available from the
underlying data files, anyway). Whether the corresponding module in the
``evedata`` package will become a true superset of this module remains to be
seen.


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


Array channels
--------------

Array channels in their general form are channels collecting 1D data.
Typical devices used here are MCAs, but oscilloscopes and vector signal
analysers (VSA) would be other typical array channels. Hence, for these
quite different types of array channels, distinct subclasses of the
generic :class:`ArrayChannelData` class exist, see
:numref:`Fig. %s <fig-uml_arraychannel_api>`.


.. _fig-uml_arraychannel_api:

.. figure:: /uml/arraychannel.*
    :align: center
    :width: 500px

    Preliminary data model for the :class:`ArrayChannelData` classes. The
    basic hierarchy is identical to :numref:`Fig. %s
    <fig-uml_evefile.data_api>`. Details for the
    :class:`MCAChannelData` class can be found in :numref:`Fig. %s
    <fig-uml_mcachannel_api>`.


Multi Channel Analysers (MCA) generally collect 1D data and typically have
separate regions of interest (ROI) defined, containing the sum of the
counts for the given region. For the EPICS MCA record,
see https://millenia.cars.aps.anl.gov/software/epics/mcaRecord.html.


.. _fig-uml_mcachannel_api:

.. figure:: /uml/mcachannel.*
    :align: center
    :width: 750px

    Preliminary data model for the :class:`MCAChannelData` classes. The basic
    hierarchy is identical to :numref:`Fig. %s
    <fig-uml_evefile.data_api>`, and here, the relevant part of the
    metadata class hierarchy from :numref:`Fig. %s
    <fig-uml_evefile_entities_metadata>` is shown as well. Separating the
    :class:`MCAChannelCalibration
    <evefile.entities.metadata.MCAChannelCalibration>` class from the
    :class:`ArrayChannelMetadata
    <evefile.entities.metadata.ArrayChannelMetadata>` allows to
    add distinct behaviour, *e.g.* creating calibration curves from the
    parameters.


Note: The scalar attributes for ArrayChannelROIs will currently be saved
as snapshots regardless of whether the actual ROI has been defined/used.
Hence, the evefile package needs to decide based on the existence of the
actual data whether to create a ROI object and attach it to
:class:`ArrayChannelData`.

The calibration parameters are needed to convert the *x* axis of the MCA
spectrum into a real energy axis. Hence,
the :class:`MCAChannelCalibration
<evefile.entities.metadata.MCAChannelCalibration>`
class will have methods for performing exactly this conversion. The
relationship between calibrated units (cal) and channel number (chan) is
defined as cal=CALO + chan\*CALS + chan^2\*CALQ. The first channel in the
spectrum is defined as chan=0. However, not all MCAs/SDDs have these
calibration values: Ketek SDDs seem to not have these values (internal
calibration?).

The real_time and life_time values can be used to get an idea of the
amount of pile up occurring, *i.e.* having two photons with same energy
within a short time interval reaching the detector being detected as one
photon with twice the energy. Hence, latest in the radiometry package,
distinct methods for this kind of analysis should be implemented.


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

      * :class:`ArrayChannelData`

        * :class:`MCAChannelData`

          * :class:`MCAChannelROIData`

* :class:`DataImporter`

  * :class:`HDF5DataImporter`

* :class:`Axis`



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
import pandas as pd
from numpy import ma

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
        # List of attributes containing data
        self._data_attributes = ["data"]

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

    def show_info(self):
        """
        Print basic information regarding the contents of a data object.

        Often, it is convenient to get a brief overview of the contents of
        a data object. The output of this method currently contains the
        following sections:

        * metadata
        * options (if present)
        * fields

        The output could look similar to the following:

        .. code-block:: none

            METADATA
            name: jane

            OPTIONS
            some_option: value

            FIELDS
            data

        Here, the ``METADATA`` block simply outputs what you would get with

        .. code-block::

            print(data.metadata)

        If options are present, then the keys of the :attr:`options` dict
        are returned in the ``OPTIONS`` block. Finally, the ``FIELDS`` block
        provides an overview of all the attributes containing some kind of
        data. This will differ depending on the type of data you are looking
        at.
        """
        print("METADATA")
        print(self.metadata)
        if self.options:
            print("\nOPTIONS")
            for key in self.options:
                print(key)
        print("\nFIELDS")
        for item in dir(self):
            if (
                not item.startswith("_")
                and not callable(getattr(self, item))
                and item not in ["importer", "metadata", "options"]
            ):
                print(item)

    def get_dataframe(self):
        """
        Retrieve Pandas DataFrame with data as column.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as column.

        """
        if self.data is not None:
            index = np.linspace(1, self.data.size, self.data.size)
        else:
            index = [0]
        dataframe = pd.DataFrame(
            {item: getattr(self, item) for item in self._data_attributes},
            index=index,
        )
        return dataframe


class Axis:
    """Axis for data.

    An axis contains always both, numerical values and the metadata
    necessary to create axis labels and to make sense of the numerical
    information.

    Attributes
    ----------
    quantity : :class:`str`
        quantity of the numerical data, usually used as first part of an
        automatically generated axis label

    unit : :class:`str`
        unit of the numerical data, usually used as second part of an
        automatically generated axis label

    symbol : :class:`str`
        symbol for the quantity of the numerical data, usually used as first
        part of an automatically generated axis label

    label : :class:`str`
        manual label for the axis, particularly useful in cases where no
        quantity and unit are provided or should be overwritten.


    .. note::
        There are three alternative ways of writing axis labels, one with
        using the quantity name and the unit, one with using the quantity
        symbol and the unit, and one using both, quantity name and symbol,
        usually separated by comma. Quantity and unit shall always be
        separated by a slash. Which way you prefer is a matter of personal
        taste and given context.


    Raises
    ------
    ValueError
        Raised when trying to set axis values to another type than numpy array
    IndexError
        Raised when trying to set axis values to an array with more than one
        dimension.
        Raised if index does not have the same length as values.


    .. versionadded:: 0.2

    """

    def __init__(self):
        super().__init__()
        self._values = np.zeros(0)
        self.quantity = ""
        self.symbol = ""
        self.unit = ""
        self.label = ""

    @property
    def values(self):
        """
        Get or set the numerical axis values.

        Values require to be a one-dimensional numpy array. Trying to set
        values to either a different type that cannot be converted to a
        numpy array or a numpy array with more than one dimension will raise
        a corresponding error.

        Raises
        ------
        ValueError
            Raised if axis values are of wrong type
        IndexError
            Raised if axis values are of wrong dimension, i.e. not a vector

        """
        return self._values

    @values.setter
    def values(self, values):
        if not isinstance(values, type(self._values)):
            values = np.asarray(values)
            if (
                not isinstance(values, type(self._values))
                or values.dtype != self._values.dtype
            ):
                raise ValueError(
                    f"Wrong type: expected {self._values.dtype}, "
                    f"got {values.dtype}"
                )
        if values.ndim > 1:
            raise IndexError("Values need to be one-dimensional")
        self._values = values


class MonitorData(Data):
    """
    Data from devices monitored, but not controlled by the eve engine.

    Monitors are a concept stemming from the underlying `EPICS layer
    <https://epics-controls.org/>`_ and are closely related to telemetry in
    general. In short: You register a certain "device", record an initial
    value, and from then on only changes to this value (together with a
    timestamp). This allows you to record any relevant changes in your setup
    with minimal overhead and data storage.

    In contrast to :class:`MeasureData`, :class:`MonitorData` do not have
    a position as primary axis, but a timestamp in milliseconds, *i.e.*,
    the :attr:`milliseconds` attribute. This means that without further ado,
    you cannot plot monitor data against other data.


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

    def get_dataframe(self):
        """
        Retrieve Pandas DataFrame with data as column.

        The index is named "milliseconds" and contains the values of the
        :attr:`milliseconds` attribute of the data object.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as column.

        """
        dataframe = super().get_dataframe()
        if self.milliseconds.ndim:
            dataframe.index = self.milliseconds
        dataframe.index.name = "milliseconds"
        return dataframe


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

    def get_dataframe(self):
        """
        Retrieve Pandas DataFrame with data as column.

        The index is named "position" and contains the values of the
        :attr:`position_counts` attribute of the data object.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as column.

        """
        dataframe = super().get_dataframe()
        if self.position_counts is not None and self.position_counts.ndim:
            dataframe.index = self.position_counts
        dataframe.index.name = "position"
        return dataframe

    def join(self, positions=None):
        """
        Perform a left join of the data on the provided list of positions.

        The main "quantisation" axis of the values for a device and the
        common reference is the list of positions. To sensibly compare the
        data of different devices or plot different device data against each
        other, the data need to be harmonised, *i.e.* share a common set of
        positions as indices.

        If positions are not present in the original data, by default,
        the corresponding entries will be masked and the :attr:`data`
        attribute converted into a :class:`numpy.ma.MaskedArray`.

        The reason for not using "NaN" (not a number) is, in short,
        that "NaN" is only defined for floating point numbers, but neither
        integers nor non-numeric values. Data, however, could generally
        contain values that are *not* floating point numbers. For a more
        detailed discussion, see the :mod:`evefile.controllers.joining`
        module.

        .. note::

            The method will *alter* the data and positions of the underlying
            :obj:`MeasureData` object. Hence, make sure to make a copy if
            this is not your intended use case.


        Parameters
        ----------
        positions : :class:`numpy.ndarray`
            Array with positions the data should be mapped to.

        Raises
        ------
        ValueError
            Raised if no positions are provided

        """
        if positions is None:
            raise ValueError("No positions provided")
        for item in self._data_attributes:
            data_ = getattr(self, item)
            if len(positions) < len(self.position_counts):
                # pylint: disable=unsubscriptable-object
                data_ = data_[
                    np.searchsorted(self.position_counts, positions).astype(
                        np.int64
                    )
                ]
            elif len(positions) > len(self.position_counts):
                original_values = data_
                data_ = ma.masked_array(np.zeros(len(positions)))
                data_ = ma.masked_array(data_)
                new_positions = np.setdiff1d(positions, self.position_counts)
                data_[
                    np.searchsorted(positions, self.position_counts).astype(
                        np.int64
                    )
                ] = original_values
                data_[
                    np.searchsorted(positions, new_positions).astype(np.int64)
                ] = ma.masked
            setattr(self, item, data_)
        self.position_counts = positions

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

    def join(self, positions=None):
        """
        Perform a left join of the data on the provided list of positions.

        The main "quantisation" axis of the values for a device and the
        common reference is the list of positions. To sensibly compare the
        data of different devices or plot different device data against each
        other, the data need to be harmonised, *i.e.* share a common set of
        positions as indices.

        If positions are not present in the original data, the previous
        value present is automatically taken for this position. This is a
        valid assumption, as the underlying EPICS monitors only record a
        new value if the actual value has changed.

        .. note::

            The method will *alter* the data and positions of the underlying
            :obj:`DeviceData` object. Hence, make sure to make a copy if
            this is not your intended use case.


        Parameters
        ----------
        positions : :class:`numpy.ndarray`
            Array with positions the data should be mapped to.

        Raises
        ------
        ValueError
            Raised if no positions are provided

        """
        if positions is None:
            raise ValueError("No positions provided")
        new_positions = (
            np.searchsorted(self.position_counts, positions, side="right") - 1
        )
        self.position_counts = positions
        self.data = self.data[new_positions]


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

    def join(self, positions=None, fill=False, snapshot=None):
        """
        Perform a left join of the data on the provided list of positions.

        The main "quantisation" axis of the values for a device and the
        common reference is the list of positions. To sensibly compare the
        data of different devices or plot different device data against each
        other, the data need to be harmonised, *i.e.* share a common set of
        positions as indices.

        If positions are not present in the original data, by default,
        the corresponding entries will be masked and the :attr:`data`
        attribute converted into a :class:`numpy.ma.MaskedArray`.

        The reason for not using "NaN" (not a number) is, in short,
        that "NaN" is only defined for floating point numbers, but neither
        integers nor non-numeric values. Data, however, could generally
        contain values that are *not* floating point numbers. For a more
        detailed discussion, see the :mod:`evefile.controllers.joining`
        module.

        If a snapshot preceding a non-existing position is available,
        the value from this snapshot is automatically taken for the given
        position.

        .. note::

            The method will *alter* the data and positions of the underlying
            :obj:`MeasureData` object. Hence, make sure to make a copy if
            this is not your intended use case.


        Parameters
        ----------
        positions : :class:`numpy.ndarray`
            Array with positions the data should be mapped to.

        fill : :class:`bool`
            Whether to fill missing positions with previous values.

            Only in case a previous value exists for a given position (or a
            snapshot containing a previous value is provided as additional
            parameter), filling for the position will be performed.
            Otherwise, the position is masked.

        snapshot : :class:`AxisData`
            Snapshot data corresponding to the original :obj:`AxisData` object.

        Raises
        ------
        ValueError
            Raised if no positions are provided

        """
        if snapshot is not None:
            fill = True
        if not fill:
            super().join(positions=positions)
        else:
            if snapshot:
                snapshot.get_data()
                insert_positions = np.searchsorted(
                    self.position_counts,
                    snapshot.position_counts,
                )
                self.data = np.insert(
                    self.data,
                    insert_positions,
                    snapshot.data,
                )
                self.position_counts = np.insert(
                    self.position_counts,
                    insert_positions,
                    snapshot.position_counts,
                )
            new_positions = (
                np.searchsorted(self.position_counts, positions, side="right")
                - 1
            )
            self.position_counts = positions
            self.data = self.data[new_positions]
            if np.where(new_positions < 0)[0].size:
                self.data = ma.masked_array(self.data)
                self.data[np.where(new_positions < 0)] = ma.masked


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
        self._attempts = None
        self._data_attributes = ["data", "attempts"]

    @property
    def attempts(self):
        """
        Number of attempts needed until final data were recorded.

        Returns
        -------
        attempts : :class:`numpy.ndarray`
            Number of attempts

        """
        if self._attempts is None:
            self.get_data()
        return self._attempts

    @attempts.setter
    def attempts(self, attempts=None):
        self._attempts = attempts

    @property
    def mean(self):
        """
        Mean values for channel data.

        Returns
        -------
        mean : :class:`numpy.ndarray`
            The mean of the values recorded.

            As at least up to eveH5 v7.x only the averaged values are stored
            in the HDF5 file, this simply returns the values stored
            in :attr:`data`.

        """
        return self.data

    def get_dataframe(self):  # pylint: disable=useless-parent-delegation
        """
        Retrieve Pandas DataFrame with data as columns.

        The DataFrame contains two columns, each corresponding to the
        respective attribute of the class:

        * data
        * attempts

        The index is named "position" and contains the values of the
        :attr:`position_counts` attribute of the data object.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as columns.

        """
        return super().get_dataframe()


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
        self._counts = None
        self._std = None
        self._data_attributes = ["data", "counts", "std"]

    @property
    def counts(self):
        """
        The number of values measured in the given time interval.

        Returns
        -------
        counts : :class:`numpy.ndarray`
            Number of values measured in the given time interval

        """
        if self._counts is None:
            self.get_data()
        return self._counts

    @counts.setter
    def counts(self, counts=None):
        self._counts = counts

    @property
    def std(self):
        """
        Standard deviation values for channel data.

        Returns
        -------
        std : :class:`numpy.ndarray`
            Standard deviation values for channel data.

        """
        if self._std is None:
            self.get_data()
        return self._std

    @std.setter
    def std(self, std=None):
        self._std = std

    @property
    def mean(self):
        """
        Mean values for channel data.

        Returns
        -------
        mean : :class:`numpy.ndarray`
            The mean of the values measured in the given time interval.

            As at least up to eveH5 v7.x only the averaged values are stored
            in the HDF5 file, this simply returns the values stored
            in :attr:`data`.

        """
        return self.data

    def get_dataframe(self):  # pylint: disable=useless-parent-delegation
        """
        Retrieve Pandas DataFrame with data as columns.

        The DataFrame contains three columns, each corresponding to the
        respective attribute of the class:

        * data
        * counts
        * std

        The index is named "position" and contains the values of the
        :attr:`position_counts` attribute of the data object.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as columns.

        """
        return super().get_dataframe()


class NormalizedChannelData:
    """
    Mixin class (interface) for normalized channel data.

    0D channels can be normalized by the data of another 0D channel,
    *i.e.* by dividing its values by the values of the normalizing channel.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.AreaChannelMetadata`
        Relevant metadata for normalization.


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
        self._normalized_data = None
        self._normalizing_data = None

    @property
    def normalized_data(self):
        """
        Data that have been normalized.

        Normalization takes place by dividing by the values of the
        normalizing channel.

        Returns
        -------
        normalized_data : Any
            Data that have been normalized.

        """
        return self._normalized_data

    @normalized_data.setter
    def normalized_data(self, normalized_data=None):
        self._normalized_data = normalized_data

    @property
    def normalizing_data(self):
        """
        Data used for normalization.

        Returns
        -------
        normalized_data : Any
            Data used for normalization.

        """
        return self._normalizing_data

    @normalizing_data.setter
    def normalizing_data(self, normalizing_data=None):
        self._normalizing_data = normalizing_data


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
        self._data_attributes = [
            "data",
            "normalized_data",
            "normalizing_data",
        ]

    @property
    def normalized_data(self):
        """
        Data that have been normalized.

        Normalization takes place by dividing by the values of the
        normalizing channel.

        Returns
        -------
        normalized_data : Any
            Data that have been normalized.

        """
        if self._normalized_data is None:
            self.get_data()
        return self._normalized_data

    @normalized_data.setter
    def normalized_data(self, normalized_data=None):
        self._normalized_data = normalized_data

    @property
    def normalizing_data(self):
        """
        Data used for normalization.

        Returns
        -------
        normalized_data : Any
            Data used for normalization.

        """
        if self._normalizing_data is None:
            self.get_data()
        return self._normalizing_data

    @normalizing_data.setter
    def normalizing_data(self, normalizing_data=None):
        self._normalizing_data = normalizing_data

    def get_dataframe(self):  # pylint: disable=useless-parent-delegation
        """
        Retrieve Pandas DataFrame with data as columns.

        The DataFrame contains three columns, each corresponding to the
        respective attribute of the class:

        * data
        * normalized_data
        * normalizing_data

        The index is named "position" and contains the values of the
        :attr:`position_counts` attribute of the data object.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as columns.

        """
        return super().get_dataframe()


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
        self._data_attributes = [
            "data",
            "attempts",
            "normalized_data",
            "normalizing_data",
        ]

    @property
    def normalized_data(self):
        """
        Data that have been normalized.

        Normalization takes place by dividing by the values of the
        normalizing channel.

        Returns
        -------
        normalized_data : Any
            Data that have been normalized.

        """
        if self._normalized_data is None:
            self.get_data()
        return self._normalized_data

    @normalized_data.setter
    def normalized_data(self, normalized_data=None):
        self._normalized_data = normalized_data

    @property
    def normalizing_data(self):
        """
        Data used for normalization.

        Returns
        -------
        normalized_data : Any
            Data used for normalization.

        """
        if self._normalizing_data is None:
            self.get_data()
        return self._normalizing_data

    @normalizing_data.setter
    def normalizing_data(self, normalizing_data=None):
        self._normalizing_data = normalizing_data

    def get_dataframe(self):  # pylint: disable=useless-parent-delegation
        """
        Retrieve Pandas DataFrame with data as columns.

        The DataFrame contains four columns, each corresponding to the
        respective attribute of the class:

        * data
        * attempts
        * normalized_data
        * normalizing_data

        The index is named "position" and contains the values of the
        :attr:`position_counts` attribute of the data object.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as columns.

        """
        return super().get_dataframe()


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
        self._data_attributes = [
            "data",
            "counts",
            "std",
            "normalized_data",
            "normalizing_data",
        ]

    @property
    def normalized_data(self):
        """
        Data that have been normalized.

        Normalization takes place by dividing by the values of the
        normalizing channel.

        Returns
        -------
        normalized_data : Any
            Data that have been normalized.

        """
        if self._normalized_data is None:
            self.get_data()
        return self._normalized_data

    @normalized_data.setter
    def normalized_data(self, normalized_data=None):
        self._normalized_data = normalized_data

    @property
    def normalizing_data(self):
        """
        Data used for normalization.

        Returns
        -------
        normalized_data : Any
            Data used for normalization.

        """
        if self._normalizing_data is None:
            self.get_data()
        return self._normalizing_data

    @normalizing_data.setter
    def normalizing_data(self, normalizing_data=None):
        self._normalizing_data = normalizing_data

    def get_dataframe(self):  # pylint: disable=useless-parent-delegation
        """
        Retrieve Pandas DataFrame with data as columns.

        The DataFrame contains five columns, each corresponding to the
        respective attribute of the class:

        * data
        * counts
        * std
        * normalized_data
        * normalizing_data

        The index is named "position" and contains the values of the
        :attr:`position_counts` attribute of the data object.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as columns.

        """
        return super().get_dataframe()


class ArrayChannelData(ChannelData):
    """
    Data for channels with numeric 1D data.

    Detector channels can be distinguished by the dimension of their data:

    0D
        scalar values per position, including average and interval channels
    1D
        array values, *i.e.* vectors, per position
    2D
        area values, *i.e.* images, per position

    This class represents 1D array values.

    Individual arrays are stored one per row in the :attr:`data` attribute.
    This allows for intuitive indexing of the individual arrays.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.ArrayChannelMetadata`
        Relevant metadata for the individual device.


    Examples
    --------
    The :class:`ArrayChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.


    .. versionadded:: 0.2

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.ArrayChannelMetadata()

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

        .. todo::
            * Decide whether all data need to be ordered according to their
              first axis (monitor data and measure data), and if only the
              latter, implement the sorting in the :meth:`MeasureData.get_data`
              method. Otherwise, implement it here.
            * Make this method version-aware, *i.e.* handle situation with
              new eveH5 v8 schema where data are stored as single dataset
              in HDF5, no longer as separate datasets. Should be rather
              easy, as this would mean only one importer with "data" as
              value?

        """
        for idx, importer in enumerate(self.importer):
            importer.load()
            if "data" in importer.mapping.values():
                data = importer.data[:, 0]
                if self._data is None:
                    self._data = np.ndarray(
                        [len(self.importer), len(data)], dtype=data.dtype
                    )
                self._data[idx, :] = importer.data[:, 0]

    def get_dataframe(self):
        """
        Retrieve Pandas DataFrame with data as column.

        .. important::

            While working with a Pandas DataFrame may seem convenient,
            you're loosing basically all the relevant metadata of the
            datasets. Hence, this method is rather a convenience method to
            be backwards-compatible to older interfaces, but it is
            explicitly *not* suggested for extensive use.

        Returns
        -------
        dataframe : :class:`pandas.DataFrame`
            Pandas DataFrame containing data as column.

        """
        if self.data is not None:
            index = np.arange(1, self.data.shape[0] + 1)
        else:
            index = [0]
        dataframe = pd.DataFrame(
            columns=self._data_attributes,
            index=index,
        )
        dataframe["data"] = dataframe["data"].astype(object)
        for idx, row in enumerate(index):
            dataframe.loc[row, "data"] = self.data[idx, :]
        if self.position_counts is not None and self.position_counts.ndim:
            dataframe.index = self.position_counts
        dataframe.index.name = "position"
        return dataframe


class MCAChannelData(ArrayChannelData):
    """
    Data for multichannel analyzer (MCA) channels.

    MCA channel data are usually 1D data, *i.e.* arrays or vectors.


    Attributes
    ----------
    metadata : :class:`evefile.entities.metadata.MCAChannelMetadata`
        Relevant metadata for the individual device.

    roi : :class:`list`
        List of data for the individual ROIs defined.

        Individual items in the list are objects of class
        :class:`MCAChannelROIData`.

    life_time : :class:`numpy.ndarray`
        Elapsed life time

        After a read status operation, this field contains the elapsed
        live time, as reported by the hardware.

    real_time : :class:`numpy.ndarray`
        Elapsed real time

        After a read status operation, this field contains the elapsed
        real time, as reported by the hardware.

    axis : :class:`Axis`
        Data and metadata for the x-axis of the array data

        MCAs record array data, and to make sense of the indices of the
        arrays, usually some calibration parameters are recorded that can
        be used to convert the indices of the array to an actual axis - be
        it energy or time or else.

        See :class:`evefile.entities.metadata.MCAChannelCalibration` for
        details of the calibration data that may be available for your MCA.


    Examples
    --------
    The :class:`MCAChannelData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.


    .. versionadded:: 0.2

    """

    def __init__(self):
        super().__init__()
        self.metadata = metadata.MCAChannelMetadata()
        self.roi = []
        self.life_time = np.ndarray(shape=[])
        self.real_time = np.ndarray(shape=[])
        self.axis = Axis()

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

        .. todo::
            * Decide whether all data need to be ordered according to their
              first axis (monitor data and measure data), and if only the
              latter, implement the sorting in the :meth:`MeasureData.get_data`
              method. Otherwise, implement it here.
            * Make this method version-aware, *i.e.* handle situation with
              new eveH5 v8 schema where data are stored as single dataset
              in HDF5, no longer as separate datasets. Should be rather
              easy, as this would mean only one importer with "data" as
              value?

        """
        super().get_data()
        if self._data is not None:
            indices = np.linspace(
                0, self.data.shape[1], self.data.shape[1], endpoint=False
            )
            if self.axis.values.size == 0:
                self.axis.values = (
                    self.metadata.calibration.offset
                    + indices * self.metadata.calibration.slope
                    + indices**2 * self.metadata.calibration.quadratic
                )


class MCAChannelROIData(MeasureData):
    """
    Data for an individual ROI of an MCA detector channel.

    Many MCAs allow to define one or several regions of interest (ROI).
    This class contains the relevant data for an individual ROI.


    Attributes
    ----------
    label : :class:`str`
        Label for the ROI provided by the operator.

    marker : :class:`numpy.ndarray`
        Two-element vector of integer values containing the left and right
        boundary of the ROI.


    Examples
    --------
    The :class:`MCAChannelROIData` class is not meant to be used
    directly, as any entities, but rather indirectly by means of the
    respective facades in the boundaries technical layer of the
    ``evefile`` package.
    Hence, for the time being, there are no dedicated examples how to use
    this class. Of course, you can instantiate an object as usual.


    .. versionadded:: 0.2

    """

    def __init__(self):
        super().__init__()
        self.label = ""
        self.marker = np.asarray([0, 0], dtype=int)


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

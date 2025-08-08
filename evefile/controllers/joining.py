"""
.. _evedata: https://evedata.docs.radiometry.de/

*Ensure data and axes values are commensurate and compatible.*

.. sidebar:: Contents

    .. contents::
        :local:
        :depth: 2

For each motor axis and detector channel, in the original eveH5 file only
those values appear---together with a "position" (PosCount) value---that
have actually been set or measured. Hence, the number of values (*i.e.*,
the length of the data vector) will generally be different for different
devices. To be able to plot arbitrary data against each other,
the corresponding data vectors need to be commensurate. If this is not the
case, they need to be brought to the same dimensions (*i.e.*, "joined",
originally somewhat misleadingly termed "filled").

To be exact, being commensurate is only a necessary, but not a sufficient
criterion, as not only the shape needs to be commensurate, but the indices
(in this case the positions) be identical.


A bit of history
================

In the previous interface (``EveFile``), there are four "fill modes" available
for data: NoFill, LastFill, NaNFill, LastNaNFill. From the `documentation of
eveFile <https://www.ahf.ptb.de/messpl/sw/python/common/eveFile/doc/html
/Section-Fillmode.html#evefile.Fillmode>`_:


NoFill
    "Use only data from positions where at least one axis and one channel
    have values."

    Actually, not a filling, but mathematically an intersection, or,
    in terms of relational databases, an ``SQL INNER JOIN``. In any case,
    data are *reduced*.

LastFill
    "Use all channel data and fill in the last known position for all axes
    without values."

    Similar to an ``SQL LEFT JOIN`` with data left and axes right,
    but additionally explicitly setting the missing axes values in the join
    to the last known axis value (or NaN if no last known axis value exists).

NaNFill
    "Use all axis data and fill in NaN for all channels without values."

    Similar to an ``SQL LEFT JOIN`` with axes left and data right. To be
    exact, the ``NULL`` values of the join operation will be replaced by
    ``NaN``.

LastNaNFill
    "Use all data and fill in NaN for all channels without values and fill
    in the last known position for all axes without values."

    Similar to an ``SQL OUTER JOIN``, but additionally explicitly setting
    the missing axes values in the join to the last known axis value (or
    NaN if no last known axis value exists) and replacing the ``NULL``
    values of the join operation by ``NaN``.


Besides using analogies from the SQL world, relational algebra is another
way of making the different join modi explicit. From the documentation of
``EveFile`` implemented in IDL by Marcus Michalsky:

    Depending on the given fill option certain data will not be present in
    the result. Let ``A`` be the set union of positions of all given axes
    and ``C`` the set union of positions of all given channels. Then the
    resulting position list will be as follows:

    .. code-block::

        'NoFill':      A ^ C (Intersection)
        'LastFill':    C
        'NaNFill':     A
        'LastNaNFill': A v C (set union)



Furthermore, for the Last*Fill modes, snapshots are inspected for axes
values that are newer than the last recorded axis in the main/standard
section or for initial axis values if an axis has not been set in the
main/standard section yet.


.. note::

    Note that **none of the fill modes guarantees that there are no NaNs**
    (or comparable null values) in the resulting data.


.. note::

    The concept of ``NaN`` is, strictly speaking, only defined for floats,
    not for other numeric types and not for strings. Hence, the previous
    mentioning of ``NaN`` is not entirely correct. See the section
    ":ref:`sec-missing_values`" below for further details.


.. important::

    The IDL Cruncher seems to use LastNaNFill combined with applying some
    "dirty" fixes to account for scans using MPSKIP and those scans
    "monitoring" a motor position via a pseudo-detector. The ``EveHDF``
    class (DS) uses LastNaNFill as a default as well but does *not* apply
    some additional post-processing.

    Shall fill modes be something to change in a viewer? And which fill
    modes are used in practice (and do we have any chance to find this out)?


.. note::

    Snapshot *positions* are never included in any joined array.
    Of course, snapshot *data* should be used for all fill modes except
    ``NoFill`` and ``NaNFill``. But it does not seem to make much sense to
    incorporate the snapshot *positions* into the joined data array.

    It may be the case with legacy interfaces, though, that including the
    PosCountTimer dataset results in a data array with all available
    position counts. This should be considered a bug, however, rather than
    a feature for most use cases. In context of one big table for all data
    recorded (including axes positions, channel readouts, options set,
    and parameters monitored), it might be the only sensible chance to get
    hand of the information contained in snapshots, however. Nevertheless,
    this would be something ``evefile`` should not be concerned about.


Different scenarios for data joining
====================================

There are basically two different scenarios, and currently, `evedata`_
implements only the first, while ``evefile`` will most probably need to
implement the second:

#. Plotting data

   In this case, there is always one data vector, but several possible
   axes vectors. Hence, we need only to deal with a 1..n relationship of data
   to axes.

   However, in this case, "axes" and "data" have different meanings as
   compared to motor axes and detector channels usually discussed. *I.e.*,
   axes and data can be both, motor axes and detector channels, respectively.

#. Creating the "all-knowing table"

   An arbitrary set of channels and axes (and monitors) should be joined
   in one single table for an easy overview and simple access. Besides the
   known problems of this approach (the data model underlying the
   measurements simply does not allow to be represented as a 2D table),
   it is and remains a known and important use case.

These two different scenarios may eventually result in having two
``joining`` modules in `evedata`_, one in the ``measurement`` functional
layer, and one in the ``evefile`` functional layer, identical with the one
developed here in ``evefile``.


.. _sec-missing_values:

How to deal with missing values?
================================

Depending on the concrete situation, there may be no value available to
fill a gap in an axis. Hence, how to deal with this situation?


Numeric values
--------------

For numeric values, some kind of "NaN" (not a number) could be used.

For NumPy, only floats can have a dedicated "NaN", but no other dtype.
Hence, in case of missing values, a masked array (
:class:`numpy.ma.MaskedArray`) is used and :data:`numpy.ma.masked` set
explicitly for those missing values. For all practical purposes,
this should work similar to the :data:`numpy.nan`. In particular,
when trying to plot a :class:`numpy.ma.MaskedArray`, the masked values are
simply ignored. For further details of how to work with masked arrays,
see the :mod:`numpy.ma` documentation.


Non-numeric values
------------------

First of all: Does this situation occur in reality? Yes, there are axes
with non-numeric values. But are these axes ever joined? If so,
some textual value such as "N/A" (not available) may be used.

.. note::

    The default fill value of a :class:`numpy.ma.MaskedArray` is ``N/A``,
    and this is (only) used when calling :meth:`numpy.ma.MaskedArray.filled`.
    Otherwise, the masked values are in most cases simply ignored. For an
    overview of the default fill values of masked arrays, see the
    :attr:`numpy.ma.MaskedArray.fill_value` attribute.


How to deal with monitor data?
==============================

To the best of the knowledge of this package's author, monitor data have
never been considered for data joining, as they would first need to be
mapped to position counts before joining. However, given that a mapping of
timestamps to position counts exists (see the :mod:`timestamp_mapping
<evefile.controllers.timestamp_mapping>` module), this finally needs to be
considered.

Monitors are somewhat special, as values are recorded for each change,
together with a timestamp. Furthermore, there should *always* be a reference
value recorded at the beginning of the scan (actually as soon as the scan
is loaded into the engine, and if there are further changes in the
monitored value before the scan execution starts, currently multiple
values with the identical timestamp of "-1" are recorded, meaning that the
last of these values should be used, see the discussion in the
:mod:`timestamp_mapping <evefile.controllers.timestamp_mapping>` module
for further details).

If monitor data should appear in a joined data array, it seems most
sensible to inflate the values to all position counts eventually in the
data array, but to not consider the position counts of the (mapped)
monitor datasets for determining which position counts to use for the
joined data array. This would be kind of a "LastFill" (in the terminology
discussed above) for the monitor data using the position counts of the
final joined data array previously determined for all the other datasets
(that in turn depend on the join mode, of course).


A few comments for further development
======================================

.. important::

    The classes implemented in this module are currently (2025/08/08) a
    direct copy of the corresponding module in `evedata`_, and here
    particularly from the "measurement" functional layer. However,
    the needs in ``evefile`` are different, hence even the basic
    :class:`Join` class needs to be redesigned. Further information below.
    Once this has been done, this entire section should be removed.


* Joining should take a list of data objects (or their names - both should
  be possible) as input and return a list of data objects with their data
  being commensurate.

* Joining needs to work on an arbitrary number of data objects.
  Internally, of course, they need to be distinguished between channel,
  axis, and monitor, and handled accordingly. However, this amounts to
  just one imput argument for the :meth:`Join.join` method (a list).

* As detailed for the IDL implementation of EveFile, in a first step the
  list of position counts of the final joined array needs to be
  determined, before dealing with the actual data values.

* Joining should probably take into account all available attributes,
  not only ``data``, but options as well if present. This of course only
  applies to ``evefile`` if options of devices are mapped to the
  respective data objects.


Join modes currently implemented
================================

Currently, there is exactly one join mode implemented:

* :class:`AxesLastFill`

  Inflate axes to data dimensions using last for missing value.

  If no previous axes value is available, convert the data into a
  :obj:`numpy.ma.MaskedArray` object and mask the value.

  This mode is equivalent to the "LastFill" mode described above.


For developers
==============

To implement additional join modes, create a class inheriting from the
:class:`Join` base class and implement the actual joining in the private
method ``_join()``.

There is a factory class :class:`JoinFactory` that you can ask to get a
:class:`Join` object:

.. code-block::

    factory = JoinFactory()
    join = factory.get_join(mode="AxesLastFill")

This would return an :obj:`AxesLastFill` object. For further details,
see the :class:`JoinFactory` documentation.


Module documentation
====================

"""

import logging

import numpy as np
from numpy import ma

logger = logging.getLogger(__name__)


class Join:
    """
    Base class for joining data.

    For each motor axis and detector channel, in the original eveH5 file only
    those values appear---together with a "position counter" (PosCount)
    value---that have actually been set or measured. Hence, the number of
    values (*i.e.*, the length of the data vector) will generally be different
    for different devices. To be able to plot arbitrary data against each
    other, the corresponding data vectors need to be commensurate. If this
    is not the case, they need to be brought to the same dimensions (*i.e.*,
    "joined", originally somewhat misleadingly termed "filled").

    The main "quantisation" axis of the values for a device and the
    common reference is the list of positions. Hence, to join,
    first of all the lists of positions are compared, and gaps handled
    accordingly.

    As there are different strategies how to deal with gaps in the
    positions list, generally, there will be different subclasses of the
    :class:`Join` class dealing each with a particular strategy.


    Attributes
    ----------
    evefile : :class:`evefile.boundaries.evefile.EveFile`
        EveFile object the Join should be performed for.

        Although joining is carried out for a small subset of the
        data of an EveFile object, additional information from the
        EveFile object may be necessary to perform the task.

    Parameters
    ----------
    evefile : :class:`evefile.boundaries.evefile.EveFile`
        EveFile object the join should be performed for.


    Examples
    --------
    Usually, joining takes place in the :meth:`get_joined_data()
    <evefile.boundaries.evefile.EveFile.get_joined_data>`
    method.

    To join data, in case of a detector channel and a motor axis,
    call :meth:`join` with the respective parameters:

    .. code-block::

        join = Join(evefile=my_evefile)
        data, *axes = join.join(
            data=("SimChan:01", None),
            axes=(("SimMot:02", None)),
        )

    Note the use of two variables for the return of the method, and in
    particular the use of ``*axes`` ensuring that ``axes`` is always a list
    and takes all remaining return arguments, regardless of their count.

    .. important::
        While it may be tempting to use this class on your own and work
        further with the returned arrays, you will lose all metadata and
        context. Hence, simply *don't*. Just use the interface provided by
        :class:`EveFile <evefile.boundaries.evefile.EveFile>` instead.

    """

    def __init__(self, evefile=None):
        self.evefile = evefile

    def join(self, data=None, axes=None, scan_module=""):
        """
        Harmonise data.

        The main "quantisation" axis of the values for a device and the
        common reference is the list of positions. Hence, to join,
        first of all the lists of positions are compared, and gaps handled
        accordingly.

        As there are different strategies how to deal with gaps in the
        positions list, generally, there will be different subclasses of the
        :class:`Join` class dealing each with a particular strategy.

        Parameters
        ----------
        data : :class:`tuple` | :class:`list`
            Name of the device and its attribute data are taken from.

            If the attribute is set to None, ``data`` will be used instead.

        axes : :class:`tuple` | :class:`list`
            Names of the devices and their attribute axes values are taken from.

            If an attribute is set to None, ``data`` will be used instead.

            Each element of the tuple/list is itself a two-element
            tuple/list with name and attribute.

        scan_module : :class:`str`
            Scan module ID the device belongs to

        Returns
        -------
        data : :class:`list`
            Joined data and axes values.

            The first element is always the data, the following the
            (variable number of) axes. To separate the two and always get a
            list of axes, you may call it like this:

            .. code-block::

                data, *axes = join.join(...)

        Raises
        ------
        ValueError
            Raised if no evefile is present
        ValueError
            Raised if no data are provided
        ValueError
            Raised if no axes are provided

        """
        if not self.evefile:
            raise ValueError("Need an evefile to join data.")
        if not data:
            raise ValueError("Need data to join data.")
        if not axes:
            raise ValueError("Need axes to join data.")
        return self._join(data=data, axes=axes, scan_module=scan_module)

    def _join(self, data=None, axes=None, scan_module=None):  # noqa
        return []


class AxesLastFill(Join):
    # noinspection PyUnresolvedReferences
    """
    Inflate axes to data dimensions using last for missing value.

    This was previously known as "LastFill" mode and was described as "Use
    all channel data and fill in the last known position for all axes
    without values." In SQL terms (relational database), this would be
    similar to a left join with data left and axes right, but additionally
    explicitly setting the missing axes values in the join to the last
    known axis value.

    While the terms "channel" and "axis" have different meanings than in
    context of the :mod:`joining
    <evefile.controllers.joining>` module, the behaviour is
    qualitatively similar:

    * The device used as "data" is taken as reference and its values are
      *not* changed.
    * The values of  devices used as "axes" are inflated to the same
      dimension as the data.
    * For values originally missing for an axis, the last value of the
      previous position is used.
    * If no previous value exists for a missing value, the data are
      converted into a :obj:`numpy.ma.MaskedArray` object and the values
      masked with :data:`numpy.ma.masked`.
    * The snapshots are checked for values corresponding to the axis,
      and if present, are taken into account.

    Of course, as in all cases, the (integer) positions are used as common
    reference for the values of all devices.

    .. important::
        If there is more than one snapshot, always the newest snapshot
        previous to the current axis position should be used. Check whether
        this is implemented already.

    Attributes
    ----------
    evefile : :class:`evefile.boundaries.evefile.EveFile`
        EveFile object the join should be performed for.

        Although joining is carried out for a small subset of the
        data of an EveFile object, additional information from the
        EveFile object may be necessary to perform the task, *e.g.*,
        the snapshots.

    Parameters
    ----------
    evefile : :class:`evefile.boundaries.evefile.EveFile`
        EveFile the join should be performed for.


    Examples
    --------
    See the :class:`Join` base class for examples -- and replace
    the class name accordingly.

    """

    def __init__(self, evefile=None):
        super().__init__(evefile=evefile)

    # pylint: disable-next=too-many-locals
    def _join(self, data=None, axes=None, scan_module=None):
        result = []
        data_device = self.evefile.data[data[0]]
        axes_devices = [self.evefile.data[axis[0]] for axis in axes]
        if data[1]:
            data_attribute = data[1]
        else:
            data_attribute = "data"
        data_values = getattr(data_device, data_attribute)
        result.append(data_values)
        for idx, axes_device in enumerate(axes_devices):
            if axes[idx][1]:
                axes_attribute = axes[idx][1]
            else:
                axes_attribute = "data"
            values = getattr(axes_device, axes_attribute)
            if axes[idx][0] in self.evefile.snapshots:
                self.evefile.snapshots[axes[idx][0]].get_data()
                axes_positions = np.searchsorted(
                    axes_device.position_counts,
                    self.evefile.snapshots[axes[idx][0]].position_counts,
                )
                snapshot_values = getattr(
                    self.evefile.snapshots[axes[idx][0]],
                    axes_attribute,
                )
                values = np.insert(values, axes_positions, snapshot_values)
            else:
                axes_positions = axes_device.position_counts
            positions = (
                np.digitize(data_device.position_counts, axes_positions) - 1
            )
            values = values[positions]
            # Set values to special value where no previous axis values exist
            if np.any(np.where(positions < 0)):
                values = ma.masked_array(values)
                values[np.where(positions < 0)] = ma.masked
            result.append(values)
        return result


class JoinFactory:
    """
    Factory for getting the correct join object.

    For background on the need for joining, see the documentation of the
    entire :mod:`joining <evefile.controllers.joining>` module, and
    of the :class:`Join <evefile.controllers.joining.Join>` class.

    Given a decision which type of join you would like to apply to
    your data, this factory class allows you to get the correct
    join instance without hassle. And you can even change your mind
    in between and don't have to change any code---the whole idea behind
    factories.

    Attributes
    ----------
    evefile : :class:`evefile.boundaries.evefile.EveFile`
        EveFile the join should be performed for.


    Parameters
    ----------
    evefile : :class:`evefile.boundaries.evefile.EveFile`
        EveFile the join should be performed for.


    Examples
    --------
    Getting a join object is as simple as calling a single method
    on the factory object:

    .. code-block::

        factory = JoinFactory()
        join = factory.get_join(mode="AxesLastFill")

    This will provide you with the appropriate :obj:`AxesLastFill` instance.

    As joins need a :class:`EveFile
    <evefile.boundaries.evefile.EveFile>` object,
    you can set one to the factory, and it will get added automatically to
    the join instance for you:

    .. code-block::

        factory = JoinFactory(evefile=my_evefile)
        join = factory.get_join(mode="AxesLastFill")

    Thus, when used from within a :class:`EveFile
    <evefile.boundaries.evefile.EveFile>` object,
    set the :attr:`evefile` attribute to ``self``.

    """

    def __init__(self, evefile=None):
        self.evefile = evefile

    def get_join(self, mode="Join"):
        """
        Obtain a :class:`Join` instance for a particular mode.

        If no mode is provided, this defaults to the base class. As the
        :class:`Join` does not implement any functionality, this is
        rather useless.

        If the :attr:`evefile` attribute is set, it is automatically set
        in the :obj:`Join` instance returned.

        Parameters
        ----------
        mode : :class:`str`
            Join mode to return a :class:`Join` instance for.

            Default: "Join"

        Returns
        -------
        join : :class:`Join`
            Join instance

        """
        instance = globals()[mode](evefile=self.evefile)
        return instance

"""

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
    to the last known axis value.

NaNFill
    "Use all axis data and fill in NaN for all channels without values."

    Similar to an ``SQL LEFT JOIN`` with axes left and data right. To be
    exact, the ``NULL`` values of the join operation will be replaced by
    ``NaN``.

LastNaNFill
    "Use all data and fill in NaN for all channels without values and fill
    in the last known position for all axes without values."

    Similar to an ``SQL OUTER JOIN``, but additionally explicitly setting
    the missing axes values in the join to the last known axis value and
    replacing the ``NULL`` values of the join operation by ``NaN``.


Furthermore, for the Last*Fill modes, snapshots are inspected for axes
values that are newer than the last recorded axis in the main/standard section.

Note that none of the fill modes guarantees that there are no NaNs (or
comparable null values) in the resulting data.


.. important::

    The IDL Cruncher seems to use LastNaNFill combined with applying some
    "dirty" fixes to account for scans using MPSKIP and those scans
    "monitoring" a motor position via a pseudo-detector. The ``EveHDF``
    class (DS) uses LastNaNFill as a default as well but does *not* apply
    some additional post-processing.

    Shall fill modes be something to change in a viewer? And which fill
    modes are used in practice (and do we have any chance to find this out)?


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


Join modes currently implemented
================================

Currently, there is exactly no join mode implemented:


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

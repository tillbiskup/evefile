"""
*Mapping time stamps of monitors to position counts.*

Monitor data (with time in milliseconds as primary axis) need to be mapped
to measured data (with position counts as primary axis). Mapping position
counts to time stamps is trivial (lookup), but *vice versa* is not unique
and the algorithm generally needs to be decided upon. In short:

* Monitors corresponding to motor axes should be mapped to the *next* position.
* Monitors corresponding to detector channels should be mapped to the
  *previous* position.
* For monitors corresponding to devices, there is no sensible decision
  possible.

Just to make things slightly more entertaining, up to eveH5 v7, monitor
datasets do *not* provide any hint which type (axis, channel, device) they
belong to. Hence, this decision can not be made sensibly. For safety
reasons, mapping monitors to the previous position seems sensible, as the
event could have occurred in the readout phase of the detectors (the
position is incremented after moving the axes and before triggering the
detector readout and start of nested scan modules).

Special cases that are addressed during mapping:

* Multiple values with timestamp ``-1``, *i.e.* *before* the scan has been
  started.

  All values except of the last (newest) with the special timestamp ``-1``
  will be skipped for now.

  For future developments of the measurement engine, it may be sensible to
  record timestamps for the monitor data in actual timestamps rather than
  milliseconds after the start of the scan (and in turn include actual
  timestamps in the PosCountTimer dataset as well). As monitor data will be
  recorded starting with a scan loaded into the engine, this would allow
  for using these data for actual telemetry of the conditions of the
  setup/beamline/machine.

* Multiple (identical) values with identical timestamp

  Not clear whether this situation can actually occur, but if so,
  most probably in this case only one value should be contained in the data.
  See `#7688, note 11 <https://redmine.ahf.ptb.de/issues/7688#note-11>`_ for
  details.

* Ignoring snapshot position counts

  It does not make sense to map monitor data to position counts of
  snapshots, as those position counts should *not* show up in any data
  array.

Furthermore, a requirement is that the original monitor data are retained
when converting timestamps to position counts. Hence, a new :obj:`MeasureData
<evefile.entities.data.MeasureData>` object is created upon mapping.


Module documentation
====================

"""

import copy

import numpy as np

import evefile.entities.data


class Mapper:
    """
    Map monitor datasets with timestamps to datasets with position counts.

    The eve measurement program has two different concepts for recorded
    data: datasets with position counts as primary axes (generally,
    motor axes and detector channels), and datasets for monitors that
    observe (monitor) values for changes and only record values upon a
    change. The latter have timestamps (in milliseconds since start of the
    scan) als primary axis.

    To be able to correlate monitors to position counts as primary axis,
    the datasets need to be mapped accordingly. The result of mapping a
    monitor dataset (a :obj:`evefile.entities.data.MonitorData` object) is a
    (new) :obj:`evefile.entities.data.DeviceData` object with the same
    data and metadata, but position counts instead of timestamps.


    Attributes
    ----------
    file : :class:`evefile.boundaries.evefile.EveFile`
        EveFile object the mapping should be performed for.

        Although mapping is carried out for individual monitors contained in
        the EveFile object, additional information from the EveFile object
        is necessary to perform the task.

    Parameters
    ----------
    file : :class:`evefile.boundaries.evefile.EveFile`
        EveFile object the mapping should be performed for.


    Examples
    --------
    Usually, mapping of monitor datasets to device datasets takes place from
    within the :class:`evefile.boundaries.evefile.EveFile` class.

    To map a monitor dataset (with ID ``DetP5000:gw2370700.STAT``) that is
    contained in the :attr:`monitors
    <evefile.boundaries.evefile.EveFile.monitors>` attribute of the
    :obj:`EveFile <evefile.boundaries.evefile.EveFile>` object referenced
    here with the variable ``evefile``, perform these steps:

    .. code-block::

        mapper = Mapper(file=evefile)
        device_data = mapper.map("DetP5000:gw2370700.STAT")

    This will return a device dataset in the variable ``device_data`` with
    timestamps mapped to position counts. See the :meth:`map` method for
    further details of the actual mapping.

    """

    def __init__(self, file=None):
        self.file = file

    def map(self, monitor=None):
        """
        Map monitor dataset to device data dataset.

        The device data dataset returned contains mapped position counts
        instead of the original timestamps (in milliseconds after start of
        the scan).

        .. note::

            For duplicate positions, typically values recorded before the
            start of the actual scan and hence with the "special" timestamp
            ``-1``, only the last position (and corresponding value) is taken.


        Parameters
        ----------
        monitor : :class:`str`
            ID of the monitor dataset to map

            Note that monitors do *not* have unique names. Hence, you need
            to provide the (unique) ID rather than the name.

        Returns
        -------
        device_data : :class:`evefile.entities.data.DeviceData`
            Device data with mapped position counts instead of timestamps

        Raises
        ------
        ValueError
            Raised if no evefile is present
        ValueError
            Raised if no monitor is provided

        """
        if not self.file:
            raise ValueError("Need an evefile to map data.")
        if not monitor:
            raise ValueError("Need monitor to map timestamps to positions.")
        monitor_data = self.file.monitors[monitor]
        # Need to force load data before mapping
        monitor_data.get_data()
        device_data = evefile.entities.data.DeviceData()
        device_data.metadata.copy_attributes_from(monitor_data.metadata)
        # Take only second of each duplicate value
        indices = np.where(
            np.diff(
                [
                    *monitor_data.milliseconds,
                    monitor_data.milliseconds[-1] + 1,
                ]
            )
        )
        device_data.position_counts = (
            self.file.position_timestamps.get_position(
                monitor_data.milliseconds[indices]
            )
        )
        device_data.data = copy.copy(monitor_data.data[indices])
        return device_data

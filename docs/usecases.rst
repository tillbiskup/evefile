.. _use_cases:

=========
Use cases
=========

.. sidebar:: Contents

    .. contents::
        :local:
        :depth: 1


*What does working with the evefile package feel and look like?*

This page provides just some first ideas of how working with the ``evefile`` package may look like. Further examples will be detailed elsewhere. Nevertheless, for the time being, it serves as high-level user documentation.


.. important::

    Potential users and contributors to these use cases should be clear about the scope of the ``evefile`` package. It is *not* meant to do any data processing and analysis, but rather provide the main **interface** between the the information obtained from a measurement and the actual data display and data processing and analysis. For these tasks, dedicated packages, namely `radiometry <https://docs.radiometry.de>`_ and `evedataviewer <https://evedataviewer.docs.radiometry.de>`_, are being developed.


General usage
=============

Before being able to work with the ``evefile`` package, you need to have it installed (in your local Python virtual environment):


.. code-block:: bash

    pip install evefile


See :doc:`installing` for further details. Once it is installed, you can import it in your code, as any other Python package:


.. code-block::

    import evefile


Having this done, you have direct access to the :class:`EveFile <evefile.boundaries.evefile.EveFile>` class that serves as the main user-facing interface of the entire package.


.. note::

    From here on, we assume you to have imported the ``evefile`` package as shown above. All further sections on this page require you to have done this step.


Loading an eveH5 data file
==========================

Suppose you have data measured and contained in an eveH5 file named ``my_measurement_file.h5``. Loading the contents of a this file is as simple as:


.. code-block::

    my_file = evefile.EveFile(filename="my_measurement_file.h5")


Here, ``my_file`` contains all the information contained in the data file as a hierarchy of Python objects. For more details, see the documentation of the :mod:`evefile <evefile.boundaries.evefile>` module and below.


Basic information on the file loaded
====================================

Having loaded a data file is fine, but how to quickly check whether you have chosen the correct file, and get an overview of what is contained in this file? Simply call the :meth:`show_info() <evefile.boundaries.evefile.EveFile.show_info>` method of the respective object:


.. code-block::

    my_file = evefile.EveFile(filename="my_measurement_file.h5")
    my_file.show_info()


This will output something similar to the following:


.. code-block:: none

    METADATA
                           filename: file.h5
                      eveh5_version: 7
                        eve_version: 2.0
                        xml_version: 9.2
                measurement_station: Unittest
                              start: 2024-06-03 12:01:32
                                end: 2024-06-03 12:01:37
                        description:
                         simulation: False
                     preferred_axis: SimMot:01
                  preferred_channel: SimChan:01
    preferred_normalisation_channel: SimChan:01

    LOG MESSAGES
    20250812T09:06:05: Lorem ipsum

    DATA
    foo (SimMot:01) <AxisData>
    bar (SimChan:01) <SinglePointChannelData>

    SNAPSHOTS
    bar (SimChan:01) <AxisData>
    bazfoo (SimChan:03) <AxisData>
    foo (SimMot:01) <AxisData>

    MONITORS


Of course, this output contains test data and test names, hence your output of an actual measurement file will show more sensible names. For further explanation, see the documentation of the :meth:`show_info() <evefile.boundaries.evefile.EveFile.show_info>` method.


Accessing individual file metadata
----------------------------------

You've seen the file metadata in the ``METADATA`` block in the output of the :meth:`show_info() <evefile.boundaries.evefile.EveFile.show_info>` method above. If you would want to access (programmatically) any of the metadata fields, this is of course possible as well:


.. code-block::

    my_file.metadata.eveh5_version


This would return the eveH5 version (as a string). How to know which metadata are available? Technically, the metadata are stored as fields of a :obj:`Metadata <evefile.entities.file.Metadata>` object. Hence, have a look at :class:`its documentation <evefile.entities.file.Metadata>` to see what fields are available and what their meanings are.


Accessing data
==============

Setting aside concepts such as metadata, snapshots, and monitors, motor axes that have been moved during a measurement and detector channels for which values have been recorded represent the primary data of any measurement contained in an eveH5 file. Of course, there is more complicated devices, such as multi-channel analysers (MCA) and cameras, but most often we deal with 1D arrays (vectors) of data.

.. note::

    One key concept of the ``evefile`` package is to load data only on demand, not already when loading the eveH5 file. This speeds up things, and often you are not interested in all the data contained in the eveH5 file, but only on some distinct datasets (in HDF5 language), *i.e.* certain motor axes and detector channels.


Each device (motor axis, detector channel) is represented as a dataset in the eveH5 file, and correspondingly as an instance of the :class:`Data <evefile.entities.data.Data>` class, to be exact an instance of one of its subclasses, in ``evefile``. The :obj:`EveFile <evefile.boundaries.evefile.EveFile>` object created upon loading an eveH5 file has a :attr:`data <evefile.boundaries.evefile.EveFile.data>` attribute (a :class:`dict`) with the unique IDs (rather than the "given" names) of the datasets as key and the :obj:`Data <evefile.entities.data.Data>` object as value.

How to get an overview of all the available datasets within the eveH5 file you've just loaded? There are two possibilities: Either you use the :meth:`EveFile.show_info() <evefile.boundaries.evefile.EveFile.show_info>` method shown above, or you ask the :obj:`EveFile <evefile.boundaries.evefile.EveFile>` object for the data contained therein:


.. code-block::

    my_file.get_data_names()


This will return a list of "given" names.

If you know the "given" name of a dataset of interest, you can directly ask for it, using the :meth:`EveFile.get_data() <evefile.boundaries.evefile.EveFile.get_data>` method:


.. code-block::

    current = my_file.get_data("Ring_1")


This would return the same dataset you could get by directly accessing the field of the :attr:`EveFile.data <evefile.boundaries.evefile.EveFile.data>` attribute using the corresponding ID as key:


.. code-block::

    current = my_file.data["bIICurrent:Mnt1chan1"]


If you have a look at the documentation of the :meth:`EveFile.get_data() <evefile.boundaries.evefile.EveFile.get_data>` method, you may realise that this method allows you to provide a list of names rather than a single name only. In this case, the return value will no longer be a single :obj:`Data <evefile.entities.data.Data>` object, but a list of :obj:`Data <evefile.entities.data.Data>` objects:


.. code-block::

    [axis, current] = my_file.get_data(["Sim_Motor1", "Ring_1"])


Note that in any case, the resulting data are objects of class :class:`Data <evefile.entities.data.Data>`, and in this particular case of classes :class:`AxisData <evefile.entities.data.AxisData>` and :class:`SinglePointChannelData <evefile.entities.data.SinglePointChannelData>`, respectively. Why this? Because every dataset comes not only with (mostly numerical) data, but corresponding metadata as well. And **data without metadata are useless**. So what now? How to get more information on the individual data(sets) you've just extracted from the loaded eveH5 file? Carry on reading...


Getting preferred data
----------------------

One concept of the eve measurement program is to (optionally) define a preferred axis and channel, and additionally a preferred normalisation channel. You can easily find out using the :meth:`show_info() <evefile.boundaries.evefile.EveFile.show_info>` method of an :obj:`EveFile <evefile.boundaries.evefile.EveFile>` object whether these values are set in the metadata.

If they are set, there is a convenient shortcut to just access these three datasets:


.. code-block::

    [pref_axis, pref_channel, pref_norm] = my_file.get_preferred_data()


If any of the three is missing, the corresponding value will be of type :obj:`None`.


Getting information on a dataset
================================

Suppose you had loaded a file ``measurement.h5`` and extracted two datasets named "Sim_Motor1" and "Ring_1" as follows:


.. code-block::

    my_file = evefile.EveFile(filename="measurement.h5")
    [axis, current] = my_file.get_data(["Sim_Motor1", "Ring_1"])


Now you have two datasets available, with the variable names ``axis`` and ``current``. To get more information on either of them, use their :meth:`show_info() <evefile.entities.data.Data.show_info>` method:


.. code-block::

    axis.show_info()


This would result in an output similar to the following:


.. code-block:: none

    METADATA
           name: Sim_Motor1
           unit: degrees
             id: SimMt:testrack01000
             pv: SimMt:testrack01000
    access_mode: ca
       deadband: 0.0

    FIELDS
    data
    position_counts
    set_values


The same you could do for the channel (the ring current):

.. code-block::

    current.show_info()


This would result in an output similar to the following:


.. code-block:: none

    METADATA
           name: Ring_1
           unit: mA
             id: bIICurrent:Mnt1chan1
             pv: bIICurrent:Mnt1.VAL
    access_mode: ca

    FIELDS
    data
    position_counts


What does all this tell you? Well: Every :obj:`Data <evefile.entities.data.Data>` object has metadata that are represented in the block ``METADATA`` above with their fields and field contents. Furthermore, it has a series of fields, usually ``position_counts`` and ``data``, with the latter containing the actual data and the former the position counts (the main quantisation axis of all the data of a scan). For how to access the metadata and data, keep reading.


Accessing (meta)data of a dataset
=================================

Suppose you had loaded a file ``measurement.h5`` and extracted two datasets named "Sim_Motor1" and "Ring_1" as before:


.. code-block::

    my_file = evefile.EveFile(filename="measurement.h5")
    [axis, current] = my_file.get_data(["Sim_Motor1", "Ring_1"])


Now you have two datasets available, with the variable names ``axis`` and ``current``. Every dataset is an instance of the (subclass of the) class :obj:`Data <evefile.entities.data.Data>`, with metadata and data.


Metadata
--------

Access each of the metadata fields as follows, as the metadata are an object of (a subclass of) class :class:`Metadata <evefile.entities.metadata.Metadata>`:


.. code-block::

    axis.metadata.unit


This would, for example, give you the unit (as string) corresponding to the axis values -- quite helpful for automatically creating axis labels, for example.


Data
----

Every dataset contains data, often numeric data in form of a 1D array (vector), and all datasets except monitors position counts as reference for the individual data entries.

Hence, to get access directly to the data, simply access the field (attribute) named ``data``:


.. code-block::

    axis.data


This would return an array (:class:`numpy.ndarray`) with the data.


.. important::

    While it may seem convenient to store the (numerical) data of a dataset in a separate variable, always keep the context of the :obj:`Data <evefile.entities.data.Data>` object, as otherwise, you will loose all the metadata. Remember: **Data without metadata are useless**.


Joining (aka "filling") data
============================

For each motor axis and detector channel, in the original eveH5 file only those values appear---together with a "position" (PosCount) value---that have actually been set or measured. Hence, the number of values (*i.e.*, the length of the data vector) will generally be different for different devices. To be able to plot arbitrary data against each other, the corresponding data vectors need to be commensurate. If this is not the case, they need to be brought to the same dimensions (*i.e.*, "joined", originally somewhat misleadingly termed "filled").

To be exact, being commensurate is only a necessary, but not a sufficient criterion, as not only the shape needs to be commensurate, but the indices (in this case the positions) be identical.

For further details and background on joining, see the documentation of the :mod:`joining <evefile.controllers.joining>` module. And be aware that *joining is far from being a trivial concept*.

Without further ado, if you know the names (or alternatively the IDs) of the datasets in your eveH5 file that you need to be joined, use the method :meth:`EveFile.get_joined_data() <evefile.boundaries.evefile.EveFile.get_joined_data>` and provide both, the list of names of the data(sets) and (optionally) the join mode:


.. code-block::

    [axis, current, lifetime] = my_file.get_joined_data(
        data=["Sim_Motor1", "Ring_1", "Lebensdauer_1"],
        mode="AxisOrChannelPositions"
    )


The result, as you can see here, will be as many datasets with joined data as you asked for. Each of these datasets is a subclass of :class:`MeasureData <evefile.entities.data.MeasureData>` and *a copy of the original data* contained in your :obj:`EveFile <evefile.boundaries.evefile.EveFile>` object (the beast you access via ``my_file`` in the code examples).


.. note::

    There are currently several different join modes implemented, and they have been renamed from the previous "fill modes". As said above, joining is far from trivial, and everybody using this feature is strongly advised to read the documentation available in the :mod:`joining <evefile.controllers.joining>` module.


Exporting data to a data frame
==============================


.. important::

    While working with a Pandas DataFrame (:class:`pandas.DataFrame`) may seem convenient, you're loosing basically all the relevant metadata of the datasets. Remember: **Data without metadata are useless**. Hence, this method is rather a convenience method to be backwards-compatible to older interfaces, but it is explicitly *not suggested for extensive use*.


Generally, two scenarios are possible and supported:

#. Export the data of a given dataset to a data frame.

#. Export the data of a list of datasets contained in an :obj:`EveFile <evefile.boundaries.evefile.EveFile>` object to a data frame.

Both scenarios are described in more detail below.


Export data of a single dataset to a data frame
-----------------------------------------------

Every dataset, to be exact every object of type :class:`Data <evefile.entities.data.Data>`, has a method :meth:`get_dataframe() <evefile.entities.data.Data.get_dataframe>` that returns the data contained in the dataset as :class:`pandas.DataFrame`.

A more complete example including loading an eveH5 file and retrieving datasets is given below. The key point here is the last line, calling :meth:`get_dataframe() <evefile.entities.data.Data.get_dataframe>` on the data object:


.. code-block::

    my_file = evefile.EveFile(filename="measurement.h5")
    [axis, current] = my_file.get_data(["Sim_Motor1", "Ring_1"])

    axis_df = axis.get_dataframe()


As mentioned above, the data frame will contain mostly the data, but nearly no metadata. For details of how exactly the resulting data frame looks like, consult the :meth:`get_dataframe() <evefile.entities.data.Data.get_dataframe>` method of the respective subclass of :class:`Data <evefile.entities.data.Data>`, *e.g.* :meth:`AxisData.get_dataframe() <evefile.entities.data.AxisData.get_dataframe>` or :meth:`SinglePointChannelData.get_dataframe() <evefile.entities.data.SinglePointChannelData.get_dataframe>`.


.. note::

    Please note that in case of getting a data frame for *individual* datasets, no :mod:`joining <evefile.controllers.joining>` of data will be performed before exporting the data to a :class:`pandas.DataFrame`. This is different to the situation described below where you export the data of a list of datasets to a data frame. Furthermore, in contrast to previous eveH5 interfaces, the data frames returned for more complicated channel types, such as :class:`NormalizedChannelData <evefile.entities.data.NormalizedChannelData>`, :class:`AverageChannelData <evefile.entities.data.AverageChannelData>`, and :class:`IntervalChannelData <evefile.entities.data.IntervalChannelData>`, will generally contain *less* columns, as some of the previously contained columns are scalar metadata that do *not* change for the individual values. Nevertheless, all these more complicated channel types will contain more than one column for data in the data frame.


Export data of a list of datasets to a data frame
-------------------------------------------------

While there may be some use cases for exporting the data of a single dataset to a data frame, probably the more frequent scenario is several datasets from a single eveH5 file that should be exported to a data frame for further handling.

For this purpose, the :obj:`EveFile <evefile.boundaries.evefile.EveFile>` object has a :meth:`get_dataframe() <evefile.boundaries.evefile.EveFile.get_dataframe>` method as well, taking two parameters: ``data`` is a list of names (or IDs) of datasets, and ``mode`` (optionally) defines how to join data of the individual columns. From that it is already obvious that here, two things happen:

#. Join the data of the respective datasets.

#. Export the joined data to a :obj:`pandas.DataFrame`.

Assuming again our scenario from above, where you have loaded an eveH5 file and stored the respective object in the ``my_file`` variable, getting a data frame consisting of the data of three datasets and explicitly setting the join mode looks as follows:


.. code-block::

    df = my_file.get_dataframe(
        data=["Sim_Motor1", "Ring_1", "Lebensdauer_1"],
        mode="AxisOrChannelPositions"
    )


As mentioned, previous to creating the data frame, data are joined. Hence, make sure you made yourself familiar with the concept of joining.


.. note::

    There are currently several different join modes implemented, and they have been renamed from the previous "fill modes". As said above, joining is far from trivial, and everybody using this feature is strongly advised to read the documentation available in the :mod:`joining <evefile.controllers.joining>` module.


.. important::

    Different to previous interfaces, the data frame will only contain one column per dataset, and this column comes directly from the :attr:`Data.data <evefile.entities.data.Data.data>` attribute. Hence, even for more complicated channel types, such as :class:`NormalizedChannelData <evefile.entities.data.NormalizedChannelData>`, :class:`AverageChannelData <evefile.entities.data.AverageChannelData>`, and :class:`IntervalChannelData <evefile.entities.data.IntervalChannelData>`, only one column will exist. If you need to get access to these additional data columns and you still want to use a :class:`pandas.DataFrame`, use the :meth:`Data.get_dataframe() <evefile.entities.data.Data.get_dataframe>` method of the individual dataset, as described above.



There is even one **special case** similar to what has been done in the past using previous interfaces: Getting a data frame containing the data of *all* datasets contained in an eveH5 file -- to be more exact, at least all data from the "main phase" of the scan (not including snapshots or monitors).

Although it is strongly discouraged to use this functionality -- among other things because it violates central concepts of the interface -- in its most simple (and probably most dangerous) form the call would look like:


.. code-block::

    almighty_dataframe = my_file.get_dataframe()


What are some of the problems with this approach? Here is an incomplete list:

* Loss of all relevant metadata.
* No join mode explicitly provided, hence depending on the defaults set in the method (that may change over time).
* Despite its name, the data frame is far from "almighty" and lacks relevant information.

Hence, use entirely on your own risk -- at best not at all. You have been warned... ;-)


Telemetry (I): Snapshots
========================

Most people using the eve measurement program are somewhat familiar with the concept of snapshots. Basically, a snapshot does what its name says: recording the current state of a list of devices, be it detector channels or motor axes. The most typical situation in a scan is two "snapshot modules" upstream of any other parts of the scan, one for detector channels and the other for motor axes. Thus, the state of all channels and axes defined in the current measurement station description is recorded.
Generally, it may be sensible to record a snapshot for all these devices after the actual scan has been carried out, but this needs to be discussed by those people responsible for designing scan descriptions.


Snapshots serve generally two functions:

#. Provide base values for axes.

   In case of joining data using :meth:`EveFile.get_joined_data() <evefile.boundaries.evefile.EveFile.get_joined_data>`, for axes, typically the previous values are used for positions no axes values have been recorded. Snapshots are used if available.

#. Provide telemetry data for the setup the data were recorded with.

   Snapshots regularly contain many more parameters than motor axes used and detector channels recorded. Generally, this provides a lot of telemetry data regarding the setup used for recording the data.

The first function is served by the :meth:`EveFile.get_joined_data() <evefile.boundaries.evefile.EveFile.get_joined_data>` method automatically. The second function can be served by having a look at a summary containing all snapshot data. This is the aim of the method :meth:`EveFile.get_snapshots() <evefile.boundaries.evefile.EveFile.get_snapshots>`: returning a Pandas DataFrame containing all snapshots as rows and the position counts as columns.

Getting a dataframe containing all the snapshot datasets as *rows* and the position counts as *columns* is as simple as:


.. code-block::

    my_file = evefile.EveFile(filename="measurement.h5")
    snapshots = my_file.get_snapshots()


The resulting :class:`pandas.DataFrame` can be output directly in the Python console, just calling the variable ``snapshots``. The result may look similar to the following:


.. code-block::

                                 1             2
    Sim_Filter_1      b'Undefined'           NaN
    Sim_Filter_2      b'Undefined'           NaN
    Keithley_196               NaN           NaN
    Channel/0                  NaN           0.0
    Sim_Motor1                20.0           NaN
    SimFilter                  NaN  b'Undefined'
    Ring_1                     NaN    296.249928
    Lebensdauer_1              NaN      7.756106
    TopupState                 NaN      b'decay'
    Ring_2                     NaN    296.855205
    Lebensdauer_2              NaN      7.053617
    mlsRing_1                  NaN       72.9936
    mlsLebensdauer_1           NaN     16.343343
    mlsRing_2                  NaN           0.0
    mlsLebensdauer_2           NaN           0.0
    mlsRing_3                  NaN      0.250081
    mlsLebensdauer_3           NaN      0.705209


Note that this dataframe only serves as a somewhat convenient overview table of the individual values recorded in the snapshots. There is no point in trying to plot data here, as some of the values are anyway non-numeric -- not to mention that for an axis snapshot, the channels have ``NaN`` as value and *vice versa*.

As mentioned in the heading of this use case, think of the snapshots as telemetry data, providing you with an overview of the state of your setup at a given point in time.

There is another type of telemetry data discussed in the next section: monitors. See below for details.


Telemetry (II): Working with monitors
=====================================

First a quick introduction into monitors. EPICS knows the concept of a monitor: You attach an observer to a process variable (PV) and get noticed only when the value of the observed PV changes. This concept is used within the eve measurement program as well, and you can set monitors to a large list of PVs defined in your measurement station description from within the eve GUI and eventually a scan description.

From the point of view of the eve engine, the main quantisation axis is the list of position counts -- one position reflecting a given state of all motor axes set and all detector axes read. However, position counts only exist for everything under control of the scan engine. Monitors by definition are not under control of the scan engine, but issue their updates independently whenever the value changes. This results in monitor datasets in the measurement files having timestamps (in milliseconds since start of the scan) instead of position counts. To relate the monitor data to the position counts, a mapping needs to be performed. Generally, this is non-trivial and should be different for motor axes and detector channels due to the design of the current scan engine. However, due to the lack of the necessary information stored in the data files, only one kind of mapping can be performed. For details, see the documentation of the :mod:`timestamp_mapping <evefile.controllers.timestamp_mapping>` module.

In any case, before you can sensibly work with monitors, you first need to map their timestamps to position counts. This is handled automatically for you when you use the :meth:`EveFile.get_monitors() <evefile.boundaries.evefile.EveFile.get_monitors>` method. However, before we get there, let's go step by step. First, let's load a file containing monitor data and get an overview of the file just loaded:


.. code-block::

    file = evefile.EveFile(filename="monitors.h5")
    file.show_info()


The result may look as follows:

.. code-block:: none

    METADATA
                           filename: monitors.h5
                      eveh5_version: 7.1
                        eve_version: 2.2.0
                        xml_version: 9.2
                measurement_station: TEST
                              start: 2025-05-15 15:18:10
                                end: 2025-05-15 15:20:10
                        description: testscan containing monitors
                         simulation: False
                     preferred_axis:
                  preferred_channel:
    preferred_normalisation_channel:

    LOG MESSAGES

    DATA
    Counter (Counter-mot) <AxisData>

    SNAPSHOTS

    MONITORS
    Status (DetP5000:gw2370700.STAT) <MonitorData>
    Status (DetbIICurrent:Mnt1topupState.STAT) <MonitorData>
    range (K0196:gw23728range) <MonitorData>
    Offset (P5000:gw2370700.AOFF) <MonitorData>
    Scan (P5000:gw2370700.SCAN) <MonitorData>
    range (P5000:gw23707range) <MonitorData>


As you can see already, although monitors have names, these names are *not unique*. Hence, you can never refer to monitors unequivocally by their (given) name, but only by their ID. This is most probably a design flaw, but that's not our business right now.

Getting a list of all monitor IDs of the given file is as simple as:


.. code-block::

    monitor_ids = list(file.monitors.keys())


To obtain an individual dataset of monitor data with their timestamps mapped to position counts, use the :meth:`EveFile.get_monitors() <evefile.boundaries.evefile.EveFile.get_monitors>` method:


.. code-block::

    device_data = file.get_monitors("DetP5000:gw2370700.STAT")


The resulting dataset is of type :class:`DeviceData <evefile.entities.data.DeviceData>` and can be used, *i.a.*, for joining data using the :meth:`EveFile.get_joined_data() <evefile.boundaries.evefile.EveFile.get_joined_data>` method:


.. code-block::

    joined_data = file.get_joined_data(([file.get_data("Counter"), monitor])


Similarly, you can obtain a dataframe with the monitor included:


.. code-block::

    dataframe = file.get_dataframe([file.get_data("Counter"), monitor])


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

    [axis, current] = my_file.get_data("Sim_Motor1", "Ring_1")


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
    [axis, current] = my_file.get_data("Sim_Motor1", "Ring_1")


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
    [axis, current] = my_file.get_data("Sim_Motor1", "Ring_1")


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
    [axis, current] = my_file.get_data("Sim_Motor1", "Ring_1")

    axis_df = axis.get_dataframe()


As mentioned above, the data frame will contain mostly the data, but nearly no metadata. For details of how exactly the resulting data frame looks like, consult the :meth:`get_dataframe() <evefile.entities.data.Data.get_dataframe>` method of the respective subclass of :class:`Data <evefile.entities.data.Data>`, *e.g.* :meth:`AxisData.get_dataframe() <evefile.entities.data.AxisData.get_dataframe>` or :meth:`SinglePointChannelData.get_dataframe() <evefile.entities.data.SinglePointChannelData.get_dataframe>`.


.. note::

    Please note that in case of getting a data frame for *individual* datasets, no :mod:`joining <evefile.controllers.joining>` of data will be performed before exporting the data to a :class:`pandas.DataFrame`. This is different to the situation described below where you export the data of a list of datasets to a data frame. Furthermore, in contrast to previous eveH5 interfaces, the data frames returend for more complicated channel types, such as :class:`AverageChannelData <evefile.entities.data.AverageChannelData>` and :class:`IntervalChannelData <evefile.entities.data.IntervalChannelData>`, will generally contain *less* columns, as some of the previously contained columns are scalar metadata that do *not* change for the individual values.


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


There is even one special case similar to what has been done in the past using previous interfaces: Getting a data frame containing the data of *all* datasets contained in an eveH5 file -- to be more exact, at least all data from the "main phase" of the scan (not including snapshots or monitors).

Although it is strongly discouraged to use this functionality -- among other things because it violates central concepts of the interface -- in its most simple (and probably most dangerous) form the call would look like:


.. code-block::

    almighty_dataframe = my_file.get_dataframe()


What are some of the problems with this approach? Here is an incomplete list:

* Lack of all relevant metadata.
* No join mode explicitly provided, hence depending on the defaults set in the method (that may change over time).
* Despite its name, the data frame is far from "almighty" and lacks relevant information.

Hence, use entirely on your own risk. You have been warned... ;-)


Working with monitors
=====================

(and: what are monitors, anyway?)



Further use cases
=================

For now, just a list of use cases to be detailed:

* ...
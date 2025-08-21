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

    file = evefile.EveFile(filename="my_measurement_file.h5")


Here, ``file`` contains all the information contained in the data file as a hierarchy of Python objects. For more details, see the documentation of the :mod:`evefile <evefile.boundaries.evefile>` module and below.


Basic information on the file loaded
====================================

Having loaded a data file is fine, but how to quickly check whether you have chosen the correct file, and get an overview of what is contained in this file? Simply call the :meth:`show_info() <evefile.boundaries.evefile.EveFile.show_info>` method of the respective object:


.. code-block::

    file = evefile.EveFile(filename="my_measurement_file.h5")
    file.show_info()


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


Further use cases
=================

For now, just a list of use cases to be detailed:

* loading data
* exporting data to a data frame
* joining, aka "filling"
* getting information on a dataset
* accessing (meta)data of a dataset
* working with monitors (and: what are monitors, anyway?)
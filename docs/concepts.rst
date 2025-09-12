========
Concepts
========

*Describe the concepts, as soon as they emerge more clearly.*


.. sidebar:: Contents

    .. contents::
        :local:
        :depth: 1


The `evefile` package, while primarily a Python interface to the measured data stored in HDF5 format and according to a given schema (termed eveH5 and evolved over time), does a lot more than existing interfaces. Its main focus is to provide **viable abstractions** and **familiar concepts** for radiometry people, *i.e.*, a **shared language**.


.. _sec-faithful_representation:

Faithful representation of the eveH5 file contents
==================================================

Currently, the ``eveFile`` package applies some filling to the actual data contained in an eveH5 file, hence making it difficult to get access to the data present in the file. Of course, eveH5 files can always be inspected using the ``hdfview`` program. Nevertheless, some information always gets lost when filling the data. Hence, the ``evefile`` package provides data structures that faithfully represent the entire information contained in an eveH5 file.

Why may this be helpful? While the normal user will not necessarily use this part of the ``evefile`` package, it should allow to quickly answer the question whether some problem with a measurement is due to the measurement program (*i.e.*, missing or wrong information in the eveH5 file) or due to the post-processing and analysis routines applied to these files. As different people/groups are responsible in each case, quickly and easily discriminating is a necessary prerequisite for efficient operation on both sides.


.. _sec-abstractions:

Abstractions
============

Good abstractions greatly simplify working with intrinsically complex things. Data recording and analysis is intrinsically complex, and there is no tool that can reduce this inherent complexity. We can only try to reduce the accidental, *i.e.* unnecessary complexity, read: make things no more complicated than necessary.


The famous pandas dataframe
---------------------------

The two-dimensional data table (alias pandas dataframe) is generally *not* a very useful abstraction, as it cannot cope with the intrinsic complexity of the measured data. Furthermore, the filled data array removes a lot of sometimes relevant information: When has a motor been moved? What does ``NaN`` mean? Value not available or some problem with acquiring the value? While used a lot in practice and touted by some as the one relevant representation of the data, experience shows that many of the existing problems with data handling stem from *ad hoc* approaches to overcome the serious limitations of the data table as foundational abstraction of the data model.

The ``evefile`` package provides an "export" to the pandas dataframe to somehow increase its acceptance, but with a clear warning issued that lots of information will be lost and the user is left alone. Both, `radiometry <https://docs.radiometry.de>`_ and `evedataviewer <https://evedataviewer.docs.radiometry.de>`_ packages will provide much more powerful abstractions and work with them.


Handling multiple versions
==========================

From the user's (engineer, scientist) perspective, there is no such thing as different eveH5 versions, nor is there an internal structure of these files.


.. note::

    The practice is currently different, but that is nothing the development of the ``evefile`` package and the connected infrastructure is concerned with. Eventually, there will be *one* supported interface to the data files (``evefile``) and a series of modular and capable tools that can be easily extended by the users (``radiometry``).


At least the relevant (practically occurring) versions of eveH5 files should be supported by the ``evefile`` package. Which versions these are will be the result of a detailed statistics over all measurement files present.


"""

*High-level Python object representation of eveH5 file contents.*

.. sidebar:: Contents

    .. contents::
        :local:
        :depth: 1

This module provides a high-level representation of the contents of an eveH5
file. Being a high-level, user-facing object representation, technically
speaking this module is a facade. The corresponding resource
(persistence-layer-facing interface) would be the :mod:`eveh5
<evefile.boundaries.eveh5>` module.


Overview
========

A first overview of the classes implemented in this module and their
hierarchy is given in the UML diagram below.


.. figure:: /uml/evefile.boundaries.evefile.*
    :align: center

    Class hierarchy of the :mod:`evefile.boundaries.evefile` module,
    providing the facade (user-facing interface) for an eveH5 file.
    Basically, it inherits from :class:`evefile.entities.file.File`
    and adds behaviour. Most of this behaviour is contributed by the various
    modules of the :mod:`controllers <evefile.controllers>`
    subpackage.


Key aspects
===========

While the :mod:`evefile <evefile.boundaries.evefile>` module is the
high-level interface (facade) of the ``evefile`` package,
it is still, from a functional viewpoint, close to the actual eveH5 files,
providing a faithful representation of all information contained in an eveH5
(and SCML) file. Nevertheless, it is clearly an abstraction from the actual
data files. Hence, the key characteristics of the module are:

* Stable interface to eveH5 files, regardless of their version.

  * Some features may only be available for newer eveH5 versions, though.

* Powerful abstractions on the device level.

  * Options to devices appear as attributes of the device objects, not as
    separate datasets.

* Actual **data are loaded on demand**, not when loading the file.

  * This does *not* apply to the metadata of the individual datasets.
    Those are read upon reading the file.
  * Reading data on demand should save time and resources, particularly
    for larger files.
  * Often, you are only interested in a subset of the available data.


Usage
=====

Loading the contents of a data file of a measurement may be as simple as:

.. code-block::

    from evefile.boundaries.evefile import EveFile

    evefile = EveFile()
    evefile.load(filename="my_measurement_file.h5")

Of course, you could alternatively set the filename first,
thus shortening the :meth:`load` method call:

.. code-block::

    evefile = EveFile()
    evefile.filename = "my_measurement_file.h5"
    evefile.load()

There is even a third way now: Instantiating the class already with a
given filename:

.. code-block::

    evefile = EveFile(filename="my_measurement_file.h5")
    evefile.load()

And yes, you can of course chain the object creation and loading the file
if you like. However, this leads to harder to read code and is therefore
*not* suggested.


Internals: What happens when reading an eveH5 file?
===================================================

Reading an eveH5 file is not as simple as reading contents of an HDF5 file
and present its contents as Python object hierarchy. At least, if you would
like to view, process, and analyse your data more conveniently, you should
not stop here. The idea behind the ``evedata`` package, and in parts behind
the :class:`EveFile` class, is to provide you as consumer of the data with
powerful abstractions and structured information. To this end, a series of
steps are necessary:

* Read the eveH5 file (actually, an HDF5 file).
* Get the correct :class:`VersionMapper
  <evefile.controllers.version_mapping.VersionMapper>` class.
* Map the file contents to the proper data structures provided by the
  ``evedata`` package.


Module documentation
====================

"""

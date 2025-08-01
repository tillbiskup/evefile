============
Architecture
============

Each software has some kind of architecture, and this is the place to describe it in broad terms, to make it easier for developers to get around the code. Following the scheme of a layered architecture as featured by the "Clean Architecture" (Robert Martin) or the "hexagonal architecture", alternatively known as "ports and adapters" (Alistair Cockburn), the different layers are described successively from the inside out.

Currently, the ``evefile`` package is divided into three technical layers, *i.e.* boundaries ("interfaces"), controllers, and entities (BCE). The boundaries layer contains both, the "interfaces" ("adapters") pointing to the user (facades) and those pointing to the underlying infrastructure (resources). Here, "user" can be either actual human users or other functional layers.


.. _fig-uml_evedata:

.. figure:: uml/evefile-functional-layers.*
    :align: center

    An UML package diagram of the evefile package. To hide the names of the technical layers from the user, one could think of importing the relevant classes (basically the facades) in the ``__init__.py`` files of the respective top-level functional packages.



.. admonition:: General remarks on the UML class diagrams

    The UML class diagrams in this document try to consistently follow a series of conventions listed below. This list is not meant to be exhaustive and may change over time.

    * Capitalising attribute types

      Attribute types that are default types of the (Python) language are not capitalised.

      Attribute types that are instances of self-defined classes are capitalised and spelled exactly as the corresponding class.

    * Singular and plural forms of attributes

      Scalar attributes have singular names.

      Attributes containing containers (lists, dictionaries, ...) have plural names.

    * Naming conventions

      Generally, naming conventions follow PEP8: class names are in CamelCase, attributes and methods in snake_case.

    * Attributes of enumerations

      No convention has yet been agreed upon. Possibilities would be ALLCAPS (as the attributes could be interpreted as constants) or snake_case.

    * Dictionaries

      Attributes that contain dictionaries as container have the container type followed by curly braces ``{}``, although this seems not to be part of the UML standard.



Entities
========

Entities are the innermost technical layer: everything depends on the entities, but the entities depend on nothing but themselves. Furthermore, entities may have little to no behaviour (*i.e.*, data classes). For the evefile functional layer, the entities consist of three modules: file, data, and metadata, in the order of their dependencies.


file module
-----------

Despite the opposite chain of dependencies, starting with the :mod:`file <evefile.entities.file>` module seems sensible, as its :class:`File <evefile.entities.file.File>` class represents a single eveH5 file and provides kind of an entry point.


.. figure:: uml/evefile.entities.file.*
    :align: center

    Class hierarchy of the :mod:`evefile.entities.file <evefile.entities.file>` module. The :class:`File <evefile.entities.file.File>` class is sort of the central interface to the entire subpackage, as this class provides a faithful representation of all information available from a given eveH5 file. To this end, it incorporates instances of classes of the other modules of the subpackage. Furthermore, "Scan" inherits from the identically named facade of the scan functional layer and contains the full information of the SCML file (if the SCML file is present in the eveH5 file).


Some comments (not discussions any more):

* "data", "snapshots", "monitors": lists or dicts?

  In the meantime, the three attributes are modelled as dictionaries. How about modelling them as dictionaries, with the keys being the names of the corresponding datasets (*i.e.*, the last part of the path within the HDF5 file).

* Organisation of datasets in main according to the scan module structure

  Despite the current structure of the eveH5 files, datasets will be organised and split according to their use in the different scan modules. In case no SCML is available, a "dummy" scan module will be created containing all the datasets in main.


data module
-----------

Data are organised in "datasets" within HDF5, and the :mod:`data <evefile.entities.data>` module provides the relevant entities to describe these datasets. Although currently (as of 08/2024, eve version 2.1) neither average nor interval detector channels save the individual data points, at least the former is a clear need of the engineers/scientists. Hence, the data model already respects this use case. As per position (count) there can be a variable number of measured points, the resulting array is no longer rectangular, but a "ragged array". While storing such arrays is possible directly in HDF5, the implementation within evedata is entirely independent of the actual representation in the eveH5 file.


.. _fig-uml_evedata-evefile.data:

.. figure:: uml/evefile.entities.data.*
    :align: center
    :width: 750px

    Class hierarchy of the :mod:`data <evefile.entities.data>` module. Each class has a corresponding metadata class in the :mod:`metadata <evefile.entities.metadata>` module. While in this diagram, some child classes seem to be identical, they have a different type of metadata (see the :mod:`metadata <evefile.entities.metadata>` module below). Generally, having different types serves to discriminate where necessary between detector channels and motor axes. You may click on the image for a larger view.


metadata module
---------------

Data without context (*i.e.* metadata) are mostly useless. Hence, to every class (type) of data in the evefile.data module, there exists a corresponding metadata class.


.. note::

    As compared to the UML schemata for the IDL interface, the decision of whether a certain piece of information belongs to data or metadata is slightly different here. The main reason for this is the problem in current (as of eveH5 v7) files and redefined detector channels, leading to a loss of information that needs to be changed anyway and is discussed above for the data module. With separate datasets for different detector channels, the problem is solved and the immutable metadata belong to the metadata classes (and are converted to attributes on the HDF5 level in the future scheme, v8).


.. _fig-uml_evefile_entities_metadata:

.. figure:: uml/evefile.entities.metadata.*
    :align: center
    :width: 750px

    Class hierarchy of the evefile.metadata module. Each concrete class in the evefile.data module has a corresponding metadata class in this module. You may click on the image for a larger view.


A note on the :class:`AbstractDeviceMetadata <evefile.entities.metadata.AbstractDeviceMetadata>` interface class: The eveH5 dataset corresponding to the TimestampMetadata class is special in sense of having no PV and transport type nor an id. Several options have been considered to address this problem:

#. Moving these three attributes down the line and copying them multiple times (feels bad).
#. Leaving the attributes blank for the "special" dataset (feels bad, too).
#. Introduce another class in the hierarchy, breaking the parallel to the Data class hierarchy (potentially confusing).
#. Create a mixin class (abstract interface) with the three attributes and use multiple inheritance/implements.

As obvious from the UML diagram, the last option has been chosen. The name "DeviceMetadata" clearly distinguishes actual devices from datasets not containing data read from some instrument.


Controllers
===========

Code in the controllers technical layer operate on the entities and provide the required behaviour (the "business logic").

What may be in here:

* Mapping different versions of eveH5 files to the entities
* Mapping timestamps to position counts
* Joining (aka "filling")


version_mapping module
----------------------

For details, see the documentation of the :mod:`version_mapping <evefile.controllers.version_mapping>` module.

Being version agnostic with respect to eveH5 schema versions is a central aspect of the evedata package. This requires facilities mapping the actual eveH5 files to the data model provided by the entities technical layer of the evefile subpackage. The :class:`EveFile <evefile.boundaries.evefile.EveFile>` facade obtains the correct :class:`VersionMapper <evefile.controllers.version_mapping.VersionMapper>` object via the :class:`VersionMapperFactory  <evefile.controllers.version_mapping.VersionMapperFactory>`, providing an :class:`HDF5File  <evefile.boundaries.eveh5.HDF5File>` resource object to the factory. It is the duty of the factory to obtain the "version" attribute from the :class:`HDF5File  <evefile.boundaries.eveh5.HDF5File>` object (possibly requiring to explicitly get the attributes of the root group of the :class:`HDF5File  <evefile.boundaries.eveh5.HDF5File>` object).


.. figure:: uml/evefile.controllers.version_mapping.*
    :align: center

    Class hierarchy of the evefile.controllers.version_mapping module, providing the functionality to map different eveH5 file schemas to the data structure provided by the :class:`HDF5File  <evefile.boundaries.eveh5.HDF5File>` class. The :class:`VersionMapperFactory  <evefile.controllers.version_mapping.VersionMapperFactory>` is used to get the correct mapper for a given eveH5 file. For each eveH5 schema version, there exists an individual ``VersionMapperVx`` class dealing with the version-specific mapping. The idea behind the ``Mapping`` class is to provide simple mappings for attributes and alike that need not be hard-coded and can be stored externally, *e.g.* in YAML files. This would make it easier to account for (simple) changes.


For each eveH5 schema version, there exists an individual ``VersionMapperVx`` class dealing with the version-specific mapping. That part of the mapping common to all versions of the eveH5 schema takes place in the :class:`VersionMapper  <evefile.controllers.version_mapping.VersionMapper>` parent class, *e.g.* removing the chain. The idea behind the ``Mapping`` class is to provide simple mappings for attributes and alike that can be stored externally, *e.g.* in YAML files. This would make it easier to account for (simple) changes.


Boundaries
==========

What may be in here:

facade:

* :class:`EveFile <evefile.boundaries.evefile.EveFile>`

resources:

* :class:`HDF5File <evefile.boundaries.eveh5.HDF5File>`


evefile module (facade)
-----------------------


.. _fig-uml_evefile_boundaries_evefile:

.. figure:: uml/evefile.boundaries.evefile.*
    :align: center

    Class hierarchy of the evefile.boundaries.evefile module, providing the facade for an eveH5 file. Currently, the basic idea is to inherit from the ``File`` entity and extend it accordingly, adding behaviour.


As per :numref:`Fig. %s <fig-uml_evefile_boundaries_evefile>`, the :class:`EveFile <evefile.boundaries.evefile.EveFile>` class inherits from the :class:`File <evefile.entities.file.File>` class of the :mod:`entities <evefile.entities>` subpackage. Reading (loading) an eveH5 file results in calling out to :meth:`HDF5File.read() <evefile.boundaries.eveh5.HDF5File.read>`, followed by mapping the eveH5 contents to the data model. Additionally, for eveH5 v7 and below, datasets for detector channels that have been redefined within one scan and scans using MPSKIP are mapped to the respective datasets accordingly. Last but not least, the corresponding SCML (and setup description, where applicable) is loaded and the metadata contained therein mapped to the metadata of the corresponding datasets.



eveh5 module (resource)
-----------------------

The aim of this module is to provide a Python representation (in form of a hierarchy of objects) of the contents of an eveH5 file that can be mapped to both, the evefile and measurement interfaces. While the Python h5py package already provides the low-level access and gets used, the eveh5 module contains Python objects that are independent of an open HDF5 file, represent the hierarchy of HDF5 items (groups and datasets), and contain the attributes of each HDF5 item in form of a Python dictionary. Furthermore, each object contains a reference to both, the original HDF5 file and the HDF5 item, thus making reading dataset data on demand as simple as possible.


.. figure:: uml/evefile.boundaries.eveh5.*
    :align: center

    Class hierarchy of the :mod:`evefile.boundaries.eveh5` module. The :class:`HDF5Item <evefile.boundaries.eveh5.HDF5Item>` class and children represent the individual HDF5 items on a Python level, similarly to the classes provided in the h5py package, but *without* requiring an open HDF5 file. Furthermore, reading actual data (dataset values) is deferred by default.


As such, the :class:`HDF5Item <evefile.boundaries.eveh5.HDF5Item>` class hierarchy shown above is pretty generic and should work with all eveH5 versions. However, it is *not* meant as a generic HDF5 interface, as it does make some assumptions based on the eveH5 file structure and format.


Some comments (not discussions any more, though):

* Reading the entire content of an eveH5 file at once vs. deferred reading?

  * Reading relevant metadata (*e.g.*, to decide about what data to plot) should be rather fast. And generally, only two "columns" will be displayed (as f(x,y) plot) at any given time -- at least if we don't radically change the way data are looked at compared to the IDL Cruncher.
  * References to the internal datasets of a given HDF5 file are stored in the corresponding Python data structures (together with the HDF5 file name). Hence, HDF5 files are closed after each operation, such as not to have open file handles that may be problematic (but see the quote from A. Collette below).
  * Plotting requires data to be properly filled, although filling will most probably not take place globally once, but on a per plot base. See the discussion on fill modes, currently below in the Dataset subpackage section.


  From the book "Python and HDF5" by Andrew Collette:

    You might wonder what happens if your program crashes with open files. If the program exits with a Python exception, don't worry! The HDF library will automatically close every open file for you when the application exits.

    -- Andrew Collette, 2014 (p. 18)

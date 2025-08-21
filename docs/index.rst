
.. image:: images/zenodo.16815768.svg
   :target: https://doi.org/10.5281/zenodo.16815768
   :align: right

=======
evefile
=======

*Transitional package to read eveH5 files containing synchrotron radiometry data recorded at BESSY/MLS in Berlin.*

Welcome! This is evefile, a Python package for **importing (synchrotron) radiometry data** obtained at one of the beamlines at **BESSY-II or MLS in Berlin**, mostly operated by the German National Metrology Institute, the `Physikalisch-Technische Bundesanstalt (PTB) <https://www.ptb.de/>`_. This package acts as transitional interface between the (eveH5) data files and the processing and analysis code. For related packages for importing, viewing, and analysing those data, have a look at the :ref:`related projects section <sec-related_projects>`.


.. note::
    This is a *transitional* package meant to be used only until the `evedata package <https://evedata.docs.radiometry.de/>`_ is considered sufficiently stable for routine use. It provides a rather low-level interface to the eveH5 data files, lacking many of the abstractions available within evedata. See :doc:`differences` for more details.


Loading the contents of a data file of a measurement is as simple as:

.. code-block::

    import evefile

    file = evefile.EveFile(filename="my_measurement_file.h5")

Here, ``file`` contains all the information contained in the data file as a hierarchy of Python objects. For more details, see the documentation of the :mod:`evefile <evefile.boundaries.evefile>` module and the :doc:`usecases` section.


Features
========

A list of features:

* Importer for eve HDF5 files (used at PTB in Berlin, Germany)

* Fully backwards-compatible to older eveH5 versions

* Complete information available that is contained in an eveH5 file

* Data are (only) loaded on demand, not when loading the file

* Powerful and intuitive abstractions, allowing for associative access to data and information – beyond a purely tabular view of the data


And to make it even more convenient for users and future-proof:

* Open source project written in Python (>= 3.9)

* Developed fully test-driven

* Extensive user and API documentation


.. warning::
    evefile is currently under active development and still considered in Beta development state. Therefore, expect frequent changes in features and public APIs that may break your own code. Nevertheless, feedback as well as feature requests are highly welcome.


Installation
============

To install the evefile package on your computer (sensibly within a Python virtual environment), open a terminal (activate your virtual environment), and type in the following:

.. code-block:: bash

    pip install evefile


.. _sec-related_projects:

Related projects
================

There is a number of related packages users of the evedata package may well be interested in, as they have a similar scope, focussing on working with synchrotron radiometry data.

* `evedata <https://evedata.docs.radiometry.de>`_

  A Python package for **importing (synchrotron) radiometry data** obtained at one of the beamlines at **BESSY-II or MLS in Berlin**, mostly operated by the German National Metrology Institute, the `Physikalisch-Technische Bundesanstalt (PTB) <https://www.ptb.de/>`_. In contrast to ``evefile``, this package will provide powerful and intuitive abstractions, allowing for associative access to data and information. Hence, ``evefile`` is only a transitional package for use until ``evedata`` is considered sufficiently stable for routine use.

* `radiometry <https://docs.radiometry.de>`_

  A Python package for **processing and analysing (synchrotron) radiometry data** in a **reproducible** and mostly **automated** fashion. Currently, it focusses on data obtained at one of the beamlines at **BESSY-II or MLS in Berlin**, mostly operated by the German National Metrology Institute, the `Physikalisch-Technische Bundesanstalt (PTB) <https://www.ptb.de/>`_.

* `evedataviewer <https://evedataviewer.docs.radiometry.de>`_

  A Python package for **graphically inspecting data** contained in EVE files, *i.e.* data **obtained at one of the beamlines at BESSY-II or MLS in Berlin**, mostly operated by the German National Metrology Institute, the `Physikalisch-Technische Bundesanstalt (PTB) <https://www.ptb.de/>`_.


License
=======

This program is free software: you can redistribute it and/or modify it under the terms of the **GPLv3 License**.



.. toctree::
   :maxdepth: 2
   :caption: User Manual:
   :hidden:

   audience
   concepts
   differences
   usecases
   installing

.. toctree::
   :maxdepth: 2
   :caption: Developers:
   :hidden:

   people
   developers
   architecture
   changelog
   roadmap
   api/index


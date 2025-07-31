=======
evefile
=======

*Transitional package to read eveH5 files containing synchrotron radiometry data recorded at BESSY/ML in Berlin.*

Welcome! This is evefile, a Python package for **importing (synchrotron) radiometry data** obtained at one of the beamlines at **BESSY-II or MLS in Berlin**, mostly operated by the German National Metrology Institute, the `Physikalisch-Technische Bundesanstalt (PTB) <https://www.ptb.de/>`_. This package acts as main interface between the (eveH5) data files and the processing and analysis code and provides abstractions that allow for a convenient and intuitive access to the data and information contained in the data files. For related packages for viewing and analysing those data, have a look at the "related projects" section below.


Features
========

A list of (planned) features:

* Importer for eve HDF5 files (used at PTB in Berlin, Germany)

* Fully backwards-compatible to older eveH5 versions


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
   usecases
   installing

.. toctree::
   :maxdepth: 2
   :caption: Developers:
   :hidden:

   people
   developers
   changelog
   roadmap
   api/index


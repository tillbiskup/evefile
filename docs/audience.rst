.. _radiometry: https://docs.radiometry.de/
.. _evedata: https://evedata.docs.radiometry.de/
.. _evedataviewer: https://evedataviewer.docs.radiometry.de/

===============
Target audience
===============

Who is the target audience of the evefile package? Is it interesting for me?


Synchrotron radiometry people at PTB Berlin
===========================================

The evedata package currently primarily addresses **radiometry** people working at the synchrotron beamlines at BESSY-II and MLS in Berlin operated by the German National Metrology Institute, the `Physikalisch-Technische Bundesanstalt (PTB) <https://www.ptb.de/>`_. Its primary goal is to provide a stable and somewhat abstract **interface to the measured data** storead primarily as HDF5 files according to a given scheme (that evolved over time). As such, it is only one (fundamental) building block in a larger digital infrastructure for data processing and analysis.


.. note::
    This is a *transitional* package meant to be used only until the `evedata`_ package is considered sufficiently stable for routine use. It provides a rather low-level interface to the eveH5 data files, lacking all the abstractions available within evedata.


If you are looking for a **data viewer tool**, aimed at conveniently inspecting data directly at the beamline, you may have a look at the `evedataviewer`_ package. And if you are interested in the **reproducible processing and analysis** of radiometry data, have a look at the `radiometry`_ package.

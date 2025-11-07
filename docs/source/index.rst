Documentation for the hdfstream python client
=============================================

This python module is used to access a service which streams the
contents of HDF5 groups, datasets and attributes over http. It
provides an interface which is based on the h5py high level API, with
some additions to allow browsing the files and directories available
on the server.

The module is hosted on pypi and can be installed with pip::

  pip install hdfstream

The source code is available at https://github.com/jchelly/hdfstream-python

See the links below for usage information and the API reference.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   connecting
   directories
   files
   groups
   datasets
   multi_slice
   advanced_indexing
   aliases
   lazy_loading
   testing
   api

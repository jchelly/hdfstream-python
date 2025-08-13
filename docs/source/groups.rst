HDF5 Groups
-----------

A HDF5 group in a file on the server is represented by a
:py:class:`hdfstream.RemoteGroup` object. The file acts like a
dictionary containing groups and datasets, so we can open a group like
this::

  remote_dir = hdfstream.open("https://localhost:8443/hdfstream", "/")
  remote_file = remote_dir["path/to/file.hdf5"]
  remote_group = remote_file["group_name"]

Groups act like dictionaries containing groups and datasets, so to
list the contents of the group::

  print(list(remote_group))

Nested groups can be accessed with::

  nested_group = remote_file["group/subgroup/subsubgroup"]

or, equivalently::

  nested_group = remote_file["group"]["subgroup"]["subsubgroup"]

The latter method may generate more requests to the server. Any
attributes of the group are available through its ``attrs`` attribute,
which is a dict of numpy ndarrays::

  print(remote_file["group"].attrs["attribute_name"])

Remote groups implement some of the same methods as a h5py.Group, so
they can be used in place of a h5py.Group in some circumstances. See
the :py:class:`hdfstream.RemoteGroup` API reference for details.

HDF5 Groups
-----------

HDF5 groups are opened by indexing a :py:class:`hdfstream.RemoteFile`
with the name of the group to open, which returns a
:py:class:`hdfstream.RemoteGroup` object. Member groups and datasets
are accessed by indexing the group with a path, similarly to h5py. For
example, to list the HDF5 objects in the file's root group::

  print(list(remote_file["/"]))

Nested groups can be accessed with::

  subsubgroup = remote_file["group/subgroup/subsubgroup"]

or, equivalently::

  subsubgroup = remote_file["group"]["subgroup"]["subsubgroup"]

although the latter method may generate more requests to the
server. Any attributes of the group are available through its ``attrs``
attribute, which is a dict of numpy ndarrays::

  print(remote_file["group"].attrs["attribute_name"])

Remote groups implement a few methods to provide limited compatibility
with h5py. See the :py:class:`hdfstream.RemoteGroup` API reference for
details.

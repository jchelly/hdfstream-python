HDF5 Datasets
-------------

Datasets are opened via the parent RemoteFile or RemoteGroup object::

  dataset = remote_file["group_name/dataset_name"]

This returns a :py:class:`hdfstream.RemoteDataset`. Using numpy style
slicing on a remote dataset returns a numpy array with the dataset
contents. E.g. to read the full dataset::

  data = dataset[...]

This will generate a http request to the server if the dataset was too
large to be downloaded with the group metadata. For large datasets (or
on slow internet connections!) you will see a progress bar while the
data is downloaded. All responses from the server are streamed to the
client in chunks, so arbitrarily large dataset slices can be
downloaded given enough time and network bandwidth.

Parts of datasets can be downloaded using numpy slicing syntax::

  partial_data = dataset[0:10]

.. note:: Slicing is somewhat limited compared to numpy: the step size
          must always be 1, so slices like `[0:10:2]` or `[10:0:-1]`
          will not work. Arrays can be used to index datasets in a
          similar manner to numpy's "advanced" indexing, but only in
          the first dimension. See :doc:`Advanced indexing
          <advanced_indexing>` for details.

If a dataset has attributes, they can be accessed through the ``attrs``
dict::

  print(dataset.attrs["attribute_name"])

Remote datasets implement some of the same methods as a h5py.Dataset,
so they can be used in place of a h5py.Dataset in some
circumstances. See the :py:class:`hdfstream.RemoteDataset` API
reference for details.

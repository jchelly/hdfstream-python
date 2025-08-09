HDF5 Datasets
-------------

Datasets are opened by indexing a RemoteFile or RemoteGroup object::

  dataset = remote_file["dataset_name"]

This returns a :py:class:`hdfstream.RemoteDataset`. Using numpy style
slicing on a remote dataset returns a numpy array with the dataset
contents. E.g. to read the full dataset::

  data = dataset[...]

This will generate a http request to the server if the dataset was too
large to be downloaded with the group metadata. For large datasets (or
on slow internet connections!) you will see a progress bar while the
data is downloaded.

Parts of datasets can be downloaded using numpy slicing syntax::

  partial_data = dataset[0:10]

If a dataset has attributes, they can be access through the `attrs` dict::

  print(dataset.attrs["attribute_name"])

Remote datasets implement a few methods to provide limited compatibility
with h5py. See the :py:class:`hdfstream.RemoteDataset` API reference for
details.

#!/bin/env python
#
#  import hdfstream.dummy as dummy
#  import numpy as np
#  x = np.arange(100)
#  dset = dummy.DummyRemoteDataset("/abc", "xyz", x)
#
#

import numpy as np

from hdfstream.remote_dataset import RemoteDataset


class DummyConnection:
    """
    Fake connection used to test indexing logic.
    Test data is just stored in a numpy array.
    """
    def __init__(self, file_path, name, data):
        self.file_path = file_path
        self.name = name
        self.data = data

    def request_slice(self, path, name, slice_descriptor):
        """
        Request a "dataset" slice. This really just returns slices from the
        numpy array passed to __init__, based on the offset and count in
        each dimension stored in slice_descriptor.
        """
        assert path == self.file_path
        assert name == self.name
        assert len(slice_descriptor) == self.data.ndim

        # Handle the case of a scalar dataset
        if len(slice_descriptor) == 0:
            return self.data[()]

        # Otherwise we have one or more slices in the first dimension
        starts = slice_descriptor[0][0]
        counts = slice_descriptor[0][1]

        if isinstance(starts, (list, np.ndarray)):
            # starts parameter is a list or array
            nr_slices = len(starts)
            starts = np.asarray(starts, dtype=int)
        else:
            # starts parameter is a scalar, so make it an array
            nr_slices = 1
            starts = np.asarray((starts,), dtype=int)

        # Get slice counts as an array of the same size as starts
        if isinstance(counts, (list, np.ndarray)):
            if len(counts) == 1:
                # In case we have a one element array instead of a scalar
                counts = np.ones_like(starts)*counts[0]
            else:
                # It's already an array
                counts = np.asarray(counts, dtype=int)
        else:
            counts = np.ones_like(starts)*counts
        assert len(starts) == len(counts)

        # Check bounds in the first dimension
        assert np.all(counts >= 0)
        assert np.all(starts >= 0)
        assert np.all(starts+counts <= self.data.shape[0])

        # Extract the dataset slices from the numpy array
        data = []
        for slice_nr in range(nr_slices):
            key = [slice(starts[slice_nr], starts[slice_nr]+counts[slice_nr], 1),]
            for i, (s,c) in enumerate(slice_descriptor[1:]):
                assert c >= 0
                assert s >= 0
                assert s + c <= self.data.shape[i]
                key.append(slice(s, s+c, 1))
            data.append(self.data[tuple(key)])
        return np.concatenate(data, axis=0)

    def request_slice_into(self, path, name, slice_descriptor, destination):
        """
        Request a dataset slice and read it into the supplied buffer.
        """
        destination[...] = self.request_slice(path, name, slice_descriptor)


class DummyRemoteDataset(RemoteDataset):
    """Fake remote dataset used to test indexing logic in RemoteDataset's
    .__getitem__. Must be initialized from a numpy ndarray.

    Set cache=True to test the case where the full dataset body was
    downloaded with the metadata so that slicing is handled by numpy.

    Set cache=False to simulate requests to the server by translating
    the __getitem__ key to a slice descriptor and extracting the
    corresponding slices from the ndarray.

    Tests should be repeated with both settings to ensure that results do
    not depend on the lazy loading parameters.
    """
    def __init__(self, file_path, name, data, cache=False):
        self.data  = data if cache else None
        self.dtype = data.dtype
        self.shape = data.shape
        self.ndim = len(self.shape)
        self.name = name
        self.file_path = file_path
        self.connection = DummyConnection(file_path, name, data)
        self.arr = data

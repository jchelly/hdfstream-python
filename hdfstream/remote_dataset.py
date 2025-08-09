#!/bin/env python

import numpy as np
import collections.abc


class RemoteDataset:
    """
    Object representing a HDF5 dataset in the remote file

    Parameters:

    connection: Connection object to use to send requests
    file_path: path to the file containing the HDF5 dataset
    name: name of the HDF5 dataset to open
    data: msgpack encoded dataset description
    """
    def __init__(self, connection, file_path, name, data, parent):

        self.connection = connection
        self.file_path = file_path
        self.name = name
        self.attrs = data["attributes"]
        self.dtype = np.dtype(data["type"])
        self.kind  = data["kind"]
        self.shape = tuple(data["shape"])
        self.ndim = len(self.shape)
        self.chunks = None
        if "data" in data:
            self.data = data["data"]
        else:
            self.data = None
        self.parent = parent

        # Compute total number of elements in the dataset
        size = 1
        for s in self.shape:
            size *= s
        self.size = size

        # Will return zero dimensional attributes as numpy scalars
        for name, arr in self.attrs.items():
            if hasattr(arr, "shape") and len(arr.shape) == 0:
                self.attrs[name] = arr[()]

    def make_slice_string(self, key):
        """
        Given a key suitable for indexing an ndarray, generate a slice
        specifier string for the web API.
        """

        # Ensure key is at least a one element sequence
        if not isinstance(key, collections.abc.Sequence):
            key = (key,)

        # Loop over dimensions
        slices = []
        dim_nr = 0
        found_ellipsis = False
        dim_mask = []
        for k in key:
            if isinstance(k, int):
                # This is a single integer index
                slices.append(str(k))
                dim_mask.append(False)
                dim_nr += 1
            elif isinstance(k, slice):
                # This is a slice. Step must be one, if specified.
                if k.step != 1 and k.step != None:
                    raise KeyError("RemoteDataset slices with step != 1 are not supported")
                # Find start and stop parameters
                slice_start = k.start if k.start is not None else 0
                slice_stop = k.stop if k.stop is not None else self.shape[dim_nr]
                dim_mask.append(True)
                slices.append(str(slice_start)+":"+str(slice_stop))
                dim_nr += 1
            elif k is Ellipsis:
                # This is an Ellipsis. Selects all elements in as many dimensions as needed.
                if found_ellipsis:
                    raise KeyError("RemoteDataset slices can only contain one Ellipsis")
                ellipsis_size = len(self.shape) - len(key) + 1
                if ellipsis_size < 0:
                    raise KeyError("RemoteDataset slice has more dimensions that the dataset")
                for i in range(ellipsis_size):
                    dim_mask.append(True)
                    slices.append("0:"+str(self.shape[dim_nr]))
                    dim_nr += 1
                found_ellipsis = True
            else:
                raise KeyError("RemoteDataset index must be integer or slice")

        # If too few slices were specified, read all elements in the remaining dimensions
        for i in range(dim_nr, len(self.shape)):
            dim_mask.append(True)
            slices.append("0:"+str(self.shape[i]))

        return ",".join(slices), np.asarray(dim_mask, dtype=bool)

    def __getitem__(self, key):
        """
        Fetch a dataset slice by indexing this object.
        """
        # Ensure key is at least a one element sequence
        if not isinstance(key, collections.abc.Sequence):
            key = (key,)

        # Convert the key to a slice string
        slice_string, dim_mask = self.make_slice_string(key)

        if self.data is None:
            # Dataset is not in memory, so request it from the server
            data = self.connection.request_slice(self.file_path, self.name, slice_string)
            # Remove dimensions where the index was a scalar
            result_dims = np.asarray(data.shape, dtype=int)[dim_mask]
            data = data.reshape(result_dims)
            # In case of scalar results, don't wrap in a numpy scalar
            if isinstance(data, np.ndarray):
                if len(data.shape) == 0:
                    return data[()]
            return data
        else:
            # Dataset was already loaded with the metadata
            return self.data[key]

    def __repr__(self):
        return f'<Remote HDF5 dataset "{self.name}" shape {self.shape}, type "{self.dtype.str}">'

    def read_direct(self, array, source_sel=None, dest_sel=None):
        """
        Mimic h5py's Dataset.read_direct() method.

        This will use the readinto() method of the http response stream to
        store data directly into the destination buffer. Only works for fixed
        length types. Will throw an exception if called on vlen data.
        """
        if source_sel is None:
            source_sel = Ellipsis
        if dest_sel is None:
            dest_sel = Ellipsis
        slice_string, _ = self.make_slice_string(source_sel)

        # Get a flattened view of the destination selection, making sure we do not make a copy
        dest_view = array[dest_sel].reshape(-1)
        if not dest_view.flags['C_CONTIGUOUS']:
            raise RuntimeError("Destination for read_direct() must be C contiguous")
        if not np.shares_memory(dest_view, array):
            raise RuntimeError("Unable to read directly into specified selection")

        # Request the data
        self.connection.request_slice_into(self.file_path, self.name, slice_string, dest_view)

    def __len__(self):
        if len(self.shape) >= 1:
            return self.shape[0]
        else:
            raise TypeError("len() is not supported for scalar datasets")

    def close(self):
        """
        There's nothing to close, but some code might expect this to exist
        """
        pass

    def request_slices(self, keys, dest=None):
        """
        Request a series of dataset slices from the server

        Returns a single array with data concatenated along the first
        axis. Intended usage is something like this:

        slices = []
        slices.append(np.s_[0:10,:])
        slices.append(np.s_[100:110,:])
        result = dataset.request_slices(slices)
        """
        # Construct the slice specifier string
        slices = []
        for key in keys:
            slice_string, dim_mask = self.make_slice_string(key)
            slices.append(slice_string)
        slice_string = ";".join(slices)

        if dest is None:
            # Make the request and return a new array
            data = self.connection.request_slice(self.file_path, self.name, slice_string)
            # Remove dimensions where the index was a scalar
            result_dims = np.asarray(data.shape, dtype=int)[dim_mask]
            return data.reshape(result_dims)
        else:
            # Download the data into the supplied destination array's buffer
            if not dest.flags['C_CONTIGUOUS']:
                raise RuntimeError("Destination for read_direct() must be C contiguous")
            self.connection.request_slice_into(self.file_path, self.name, slice_string, dest)


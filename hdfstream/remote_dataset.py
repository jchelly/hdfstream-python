#!/bin/env python

import numpy as np
import collections.abc

import hdfstream.slice_utils as su


# This limits how many slices we request from the server at once
_max_nr_slices = 16777216


class RemoteDataset:
    """
    This class represents a HDF5 dataset in a file on the server. To open a
    dataset, index the parent RemoteGroup or RemoteFile object. The class
    constructor documented here is used to implement lazy loading of HDF5
    metadata and should not usually be called directly.

    Indexing a RemoteDataset with numpy style slicing yields a numpy array
    with the dataset contents. Slices must be contiguous ranges. Indexing
    with an array is not supported.

    :param connection: connection object which stores http session information
    :type connection: hdfstream.connection.Connection
    :param file_path: virtual path of the file containing the dataset
    :type file_path: str
    :param name: name of the HDF5 dataset
    :type name: str
    :param data: decoded msgpack data describing the dataset, defaults to None
    :type data: dict, optional
    :param parent: parent HDF5 group, defaults to None
    :type parent: hdfstream.RemoteGroup, optional

    :ivar attrs: dict of HDF5 attribute values of the form {name : np.ndarray}
    :vartype attrs: dict
    :ivar dtype: data type for this dataset
    :vartype dtype: np.dtype
    :ivar shape: shape of this dataset
    :vartype shape: tuple of integers
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

    def __getitem__(self, key):
        """
        Fetch a dataset slice by indexing this object.
        """
        nd_slice = su.parse_key(self.shape, key)

        if self.data is None:
            # Data is not in memory, so we'll need to request it
            if hasattr(nd_slice, "to_generator"):
                # Might need to chunk the request if we indexed the dataset with a large array
                data = np.ndarray(nd_slice.result_shape(), dtype=self.dtype)
                offset = 0
                for n, params in nd_slice.to_generator(_max_nr_slices):
                    self.connection.request_slice_into(self.file_path, self.name, params, data[offset:offset+n,...])
                    offset += n
            else:
                # Send a single request for the data
                data = self.connection.request_slice(self.file_path, self.name, nd_slice.to_list())
            # Remove dimensions where the index was a scalar
            data = data.reshape(nd_slice.result_shape())
            # Might need to reorder the output if key included an array
            if hasattr(nd_slice, "reorder"):
                data = nd_slice.reorder(data)
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
        Read data directly into a destination buffer. This can
        save time by preventing unneccessary copying of the data but
        only works for fixed length types (e.g. integer or floating
        point data).

        Copies the data if the destination array does not have the same data
        type as the dataset.

        :param array: output array which will receive the data
        :type array: np.ndarray
        :param source_sel: selection in the source dataset as a numpy slice, defaults to None
        :type source_sel: slice or list of slices, optional
        :param dest_sel: selection in the output array as a numpy slice, defaults to None
        :type dest_sel: slice or list of slices, optional
        """
        if source_sel is None:
            source_sel = Ellipsis
        if dest_sel is None:
            dest_sel = Ellipsis

        # Parse the source selection into a tuple of slice objects
        nd_slice = su.NormalizedSlice(self.shape, source_sel)

        # Get (offset, length) pairs describing the slice to read
        slice_descriptor = nd_slice.to_list()

        # Get a view of the destination selection, making sure we do not make a copy
        dest_view = array[dest_sel]
        if not dest_view.flags['C_CONTIGUOUS']:
            raise RuntimeError("Destination for read_direct() must be C contiguous")
        if not np.shares_memory(dest_view, array):
            raise RuntimeError("Unable to read directly into specified selection")

        if array.dtype == self.dtype:
            # The data types match, so we can download directly into the destination buffer
            self.connection.request_slice_into(self.file_path, self.name, slice_descriptor, dest_view)
        else:
            # The data types are different, so we have to make a copy and let numpy convert the values
            if not np.can_cast(self.dtype, array.dtype, casting='safe'):
                raise RuntimeError("Cannot safely cast {self.dtype} to {array.dtype}")
            dest_view[...] = self.connection.request_slice(self.file_path, self.name, slice_descriptor)

    def __len__(self):
        if len(self.shape) >= 1:
            return self.shape[0]
        else:
            raise TypeError("len() is not supported for scalar datasets")

    def close(self):
        """
        Close the group. Only included for compatibility (there's nothing to close.)
        """
        pass

    def request_slices(self, slices, dest=None):
        """
        Request a series of dataset slices from the server and return a
        single array with the slices concatenated along the first
        dimension. Slices may only differ in the first dimension, must
        be in ascending order of starting index in the first dimension,
        and must not overlap. Slices must have step=1. Example usage::

          slices = []
          slices.append(np.s_[0:10,:])
          slices.append(np.s_[100:110,:])
          result = dataset.request_slices(slices)

        If the optional dest parameter is used the result is written to dest.
        Otherwise a new np.ndarray is returned.

        :param keys: list of multidimensional slices to read
        :type keys: list of tuples of slice objects
        :param dest: destination buffer to write to, defaults to None
        :type dest: np.ndarray, optional

        """
        # Parse the list of slices
        nd_slices = []
        for s in slices:
            nd_slices.append(su.NormalizedSlice(self.shape, s))

        # Make a descriptor to fetch the combined slices in one request
        multislice = su.MultiSlice(nd_slices)
        slice_descriptor = multislice.to_list()
        result_shape = multislice.result_shape()

        if dest is None:
            # Make the request and return a new array
            data = self.connection.request_slice(self.file_path, self.name, slice_descriptor)
            # Remove dimensions where the index was a scalar
            return data.reshape(result_shape)
        else:
            # Download the data into the supplied destination array's buffer
            self.connection.request_slice_into(self.file_path, self.name, slice_descriptor, dest)

    def _copy_self(self, dest, name, shallow=False, expand_soft=False, recursive=True):
        """
        Copy this dataset to a new HDF5 dataset in the specified h5py file or
        group. The parameters shallow, expand_soft and recursive are not used
        here but are present so that this method has the same signature as
        RemoteGroup._copy_self().
        """
        # Copy the dataset data. TODO: download large datasets in chunks
        dest[name] = self[...]

        # Copy any attributes on the dataset
        dataset = dest[name]
        for attr_name, attr_val in self.attrs.items():
            dataset.attrs[attr_name] = attr_val

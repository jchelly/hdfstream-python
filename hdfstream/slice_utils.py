#!/bin/env python

import numpy as np


# # Encoding an array of ints to a msgpack array
# from msgpack import Packer

# packer = Packer()
# packed = b''.join([
#     packer.pack_array_header(len(arr)),
#     *map(packer.pack, arr)
# ])

def is_integer(i):
    return isinstance(i, (int, np.integer))


def convert_list_to_array(index, size):
    """
    Given a list of integers or booleans used to index a dimension of size
    size, return a numpy array of indexes.
    """
    # Handle the zero length case first
    if len(index) == 0:
        return np.zeros(0, dtype=int)
    # Then check if we have integers or booleans
    if isinstance(index[0], bool):
        # Check that all elements are booleans
        for ind in index:
            if not isinstance(ind, bool):
                raise IndexError("Indexes in a list must all be the same type")
        # Return the array
        return np.asarray(index, dtype=bool)
    elif is_integer(index[0]):
        # Check that all elements are integers
        for ind in index:
            if not is_integer(ind):
                raise IndexError("Indexes in a list must all be the same type")
        # Return the array
        return np.asarray(index, dtype=int)
    else:
        raise IndexError("Lists of indexes must contain booleans or integers")


def ensure_integer_index_array(index, size):
    """
    Convert the input array of indexes from boolean to integer, if necessary
    """
    if len(index.shape) > 1:
        raise IndexError("Arrays used as indexes must not be multidimensional")
    if np.issubdtype(index.dtype, np.integer):
        return index # Already an array of integers
    elif np.issubdtype(index.dtype, np.bool_):
        if index.shape[0] != size:
            raise IndexError("Boolean index array is the wrong size!")
        return np.arange(size, dtype=int)[index] # convert bools to integers
    else:
        raise IndexError("Index arrays must be of integer or boolean type")


def merge_slices(starts, counts):
    """
    Given a set of slices where slice i starts at index starts[i] and contains
    counts[i] elements, merge any adjacent slices and return new starts and
    counts arrays.

    :param starts: 1D array with starting offset of each slice
    :type  starts: np.ndarray
    :param counts: 1D array with length of each slice
    :type  counts: np.ndarray

    :return: new (starts, counts) tuple with the merged slices
    :rtype: (numpy.ndarray, numpy.ndarray)
    """

    starts = np.asarray(starts, dtype=int)
    counts = np.asarray(counts, dtype=int)

    # First, eliminate any zero length slices
    keep = counts > 0
    starts = starts[keep]
    ends = starts + counts[keep]

    # Determine number of slices
    nr_slices = len(starts)
    if len(ends) != nr_slices:
        raise ValueError("starts and counts arrays must be the same size!")

    # Determine starts to keep: every starting offset which is NOT
    # equal to the end of the previous slice. Always keep the first.
    keep_start = np.ones(nr_slices, dtype=bool)
    keep_start[1:] = (starts[1:] != ends[:-1])

    # Determine ends to keep: every end offset which is NOT equal
    # to the start of the next slice. Always keep the last one.
    keep_end = np.ones(nr_slices, dtype=bool)
    keep_end[:-1] = (ends[:-1] != starts[1:])

    # Discard unwanted elements
    assert len(starts) == len(ends)
    starts = starts[keep_start]
    counts = ends[keep_end] - starts

    return starts, counts


class NormalizedSlice:

    def __init__(self, shape, key):
        """
        Class used to interpret numpy style index tuples.

        Converts the supplied key into a tuple of slices with one element for
        each dimension in the dataset. Any Ellipsis are expanded into
        one or more slice(None) and if neccessary we pad out missing dimensions
        with slice(None). Any slice(None) are then replaced with explicit
        integer ranges based on the size of the dataset.

        The index for each dimension may be an integer or a slice object.
        We might also have up to one Ellipsis in place of zero or more
        dimensions. We're only going to allow lists and arrays as the index
        in the first dimension here.

        Slices with a step size other than 1 are not supported.

        :param shape: shape of the dataset that was indexed
        :type shape: tuple of integers
        :param key: index that was requested
        :type key: tuple, list, array, integer, slice, or Ellipsis
        """

        # Mask to determine dimensions of the result: we will drop dimensions
        # where the index was a scalar, for consistency with numpy.
        self.mask = np.ones(len(shape), dtype=bool)
        self.shape = np.asarray(shape, dtype=int)
        self.rank = len(self.shape)

        # Handle the case where the dataset is a scalar. Only an empty tuple
        # or an Ellipsis is allowed here.
        if len(shape) == 0:
            if key is Ellipsis or (isinstance(key, tuple) and len(key) == 0):
                key = ()
            else:
                raise IndexError("Scalars can only be indexed with () or Ellipsis")

        # Ensure the key is wrapped in a tuple and not too long
        if not isinstance(key, tuple):
            key = (key,)
        if len(key) > len(shape):
            raise IndexError("Too many indexes!")

        # Expand out any Ellipsis by replacing with zero or more slice(None)
        nr_ellipsis = sum(item is Ellipsis for item in key)
        nr_missing = len(shape) - len(key)
        if nr_ellipsis > 1:
            raise IndexError("Index tuples may only contain one Ellipsis")
        elif nr_ellipsis == 1:
            i = key.index(Ellipsis)
            key = key[:i]+(slice(None),)*(nr_missing+1)+key[i+1:]

        # If we still don't have one entry per dimension, append some slice(None)
        nr_missing = len(shape) - len(key)
        assert nr_missing >= 0
        key = key + (slice(None),)*nr_missing

        # Should now have one entry per dimension
        assert len(key) == len(shape)

        # Validate and store the index for each dimension:
        self.keys = []
        for i, index in enumerate(key):
            if isinstance(index, slice):
                # Index is a slice object. Expand out any Nones in it.
                # Also converts negative start or stop values to positive.
                self.keys.append(slice(*index.indices(shape[i])))
            elif is_integer(index):
                # Index is a built in or numpy scalar integer
                j = int(index)
                if j < 0:
                    j += shape[i] # negative indexes count from the end
                self.keys.append(slice(j, j+1, 1))
                self.mask[i] = False
            else:
                raise IndexError("Simple slice indexes must be integer, slice, or Ellipsis")

        # Check that any slices have a step size of 1
        for key in self.keys:
            if isinstance(key, slice):
                if key.step != 1:
                    raise IndexError("Slices must have step=1")

        # Compute offset and length of the slice in each dimension
        self.start = np.zeros(self.rank, dtype=int)
        self.count = np.zeros(self.rank, dtype=int)
        for i in range(self.rank):
            self.start[i] = self.keys[i].start
            self.count[i] = max(0, self.keys[i].stop - self.keys[i].start)

    def result_shape(self):
        """
        Return the expected shape of the result of applying the index.
        Any dimensions where the key was a scalar are dropped.
        """
        return self.count[self.mask]

    def to_list(self):
        """
        Convert the list of slices to nested lists, suitable for msgpack
        encoding as the slice parameter expected by the server.
        """
        return [[int(s), int(c)] for s, c in zip(self.start, self.count)]


class MultiSlice:
    """
    Class used to generate a combined request for multiple slices

    Input is a list of NormalizedSlice objects which must be identical
    in all dimensions but the first. Slices will be concatenated along the
    first dimension.
    """
    def __init__(self, slice_list):

        # Check that we have at least one slice
        if len(slice_list) == 0:
            raise IndexError("Cannot request zero slices")

        # The dataset must not be scalar
        if slice_list[0].rank == 0:
            raise IndexError("Cannot request multiple slices of a scalar dataset")

        # Check that all of the slices can be concatenated along the first dimension:
        # they must be identical in dimensions after the first
        first_nd_slice = slice_list[0]
        for nd_slice in slice_list[1:]:
            if (np.any(first_nd_slice.start[1:] != nd_slice.start[1:]) or
                np.any(first_nd_slice.count[1:] != nd_slice.count[1:]) or
                np.any(first_nd_slice.mask[1:] != nd_slice.mask[1:])):
                raise IndexError("Slices cannot be concatenated along the first dimension")

        # Find all offsets and lengths in the first dimension
        starts = [int(nd_slice.start[0]) for nd_slice in slice_list]
        counts = [int(nd_slice.count[0]) for nd_slice in slice_list]

        # Construct slice descriptor for this set of slices
        self.descriptor = [[starts, counts]]
        for i in range(1, first_nd_slice.rank):
            self.descriptor.append([int(first_nd_slice.start[i]),
                                    int(first_nd_slice.count[i])])

        # We never drop the first dimension when concatenating slices
        self.mask = first_nd_slice.mask.copy()
        self.mask[0] = True

        # Compute shape of the result
        result_shape = first_nd_slice.count.copy()
        result_shape[0] = sum(counts)
        self._result_shape = result_shape[self.mask]

    def to_list(self):
        """
        Convert the list of slices to nested lists, suitable for msgpack
        encoding as the slice parameter expected by the server.
        """
        return self.descriptor

    def result_shape(self):
        """
        Return the expected shape of the result. Any dimensions (other than
        the first) where the key was a scalar are dropped.
        """
        return self._result_shape


class ArrayIndexedSlice:

    def __init__(self, shape, key):
        """
        This class handles the case of indexing an array with a list or
        array in the first dimension. We convert the array or list into a
        list of slices to request from the server.

        We don't allow an array as the index in any other dimension.
        """

        # Should have converted key to tuple before calling
        assert isinstance(key, tuple)

        if len(key) > len(shape):
            raise IndexError("Too many indexes")
        if not isinstance(key, tuple) or len(key) < 1:
            raise IndexError("Index should be a tuple with at least one element")

        # If the first element is a list, convert it to an array
        index = key[0]
        if isinstance(index, list):
            index = convert_list_to_array(key[0], shape[0])
        assert isinstance(index, np.ndarray)
        if len(index.shape) != 1:
            raise IndexError("Index arrays must be one dimensional")

        # If we now have a boolean mask array, convert to integer indexes
        index = ensure_integer_index_array(index, shape[0])

        # Negative indexes count from the end of the array
        is_negative = (index < 0)
        index[is_negative] += shape[0]
        assert np.all(index >= 0)

        # Ensure index elements are sorted and unique, and store the inverse so
        # we can restore the requested ordering in the output array later.
        self.inverse_index = None
        if len(index) > 1:
            if np.any(index[1:] <= index[:-1]):
                index, self.inverse_index = np.unique(index, return_inverse=True)

        # Convert to arrays of starts and counts in the first dimension:
        # Treat each index as a one element range then merge adjacent ranges.
        self.starts, self.counts = merge_slices(index, np.ones(len(index), dtype=int))

        # Interpret indexes in any remaining dimensions as simple slices
        self.nd_slice = NormalizedSlice(shape[1:], key[1:])

    def to_list(self):
        """
        Convert the list of slices to nested lists, suitable for msgpack
        encoding as the slice parameter expected by the server.
        """
        # Store arrays of starts and counts in the first dimension
        items = [[self.starts, self.counts]]

        # Store scalar start and count for each subsequent dimension
        for s, c in zip(self.nd_slice.start, self.nd_slice.count):
            items.append([int(s),int(c)])

        return items

    def to_generator(self, max_nr_slices):
        """
        Generator function which yields parameters for multiple requests.
        This is to split requests which would exceed the server's maximum
        index array size.
        """
        n = len(self.starts)
        for offset in range(0, n, max_nr_slices):
            i1 = offset
            i2 = min(offset + max_nr_slices, n)
            items = [[self.starts[i1:i2], self.counts[i1:i2]]]
            for s, c in zip(self.nd_slice.start, self.nd_slice.count):
                items.append([int(s),int(c)])
            yield (sum(self.counts[i1:i2]), items)

    def result_shape(self):
        """
        Return the expected shape of the result. Any dimensions where the key
        was a scalar are dropped. The first dimension is always an array here.
        """
        shape = np.asarray([sum(self.counts),] + [int(n) for n in self.nd_slice.result_shape()], dtype=int)
        return shape

    def reorder(self, arr):
        """
        If the index array was not sorted and unique, we may have to reorder
        the result.
        """
        if self.inverse_index is None:
            return arr
        else:
            return arr[self.inverse_index,...]

def parse_key(shape, key):
    """
    Interpret key as a NormalizedSlice or ArrayIndexedSlice
    """
    if isinstance(key, (np.ndarray, list)):
        # Index is a single list or array, so wrap it in a tuple
        return ArrayIndexedSlice(shape, (key,))
    if isinstance(key, tuple) and len(key) > 0 and isinstance(key[0], (np.ndarray, list)):
        # Index is a tuple with a list or array as the first element
        return ArrayIndexedSlice(shape, key)
    else:
        # Index is something else
        return NormalizedSlice(shape, key)

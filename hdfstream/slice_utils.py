#!/bin/env python

import numpy as np

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


class DatasetIndex:

    def __init__(self, shape, key):
        """
        Class used to convert numpy style index tuples into an appropriate format
        for the web service.

        Converts the supplied key into a tuple of slices with one element for
        each dimension in the dataset. Any Ellipsis are expanded into
        one or more slice(None) and if neccessary we pad out missing dimensions
        with slice(None).

        The index for each dimension may be any of:

        * Integer
        * Slice object
        * List of indexes
        * Array of indexes

        We might also have up to one Ellipsis in place of zero or more
        dimensions. We're only going to allow lists and arrays as the index
        in the first dimension here. Boolean indexing is not supported.

        :param shape: shape of the dataset that was indexed
        :type shape: tuple of integers
        :param key: index that was requested
        :type key: tuple, list, array, integer, slice, or Ellipsis
        """

        # Mask to determine dimensions of the result: we will drop dimensions
        # where the index was a scalar, for consistency with numpy.
        self.mask = np.ones(len(shape), dtype=bool)

        # Handle the case where the dataset is a scalar. Only an empty tuple
        # or an Ellipsis is allowed here.
        if len(shape) == 0:
            if key is Ellipsis or (isinstance(key, tuple) and len(key) == 0):
                return ()
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
            key = key[:i]+(slice(None),)*nr_missing+key[i+1:]

        # If we still don't have one entry per dimension, append some slice(None)
        nr_missing = len(shape) - len(key)
        assert nr_missing >= 0
        key = key + (slice(None),)*nr_missing

        # Should now have one entry per dimension
        assert len(key) == len(shape)

        # Validate and store the index for each dimension:
        # After this the first dimension may have a slice object or an array.
        # The remaining dimensions (if any) will all have slice objects.
        self.keys = []
        for i, index in enumerate(key):
            if isinstance(index, list):
                index = convert_list_to_array(index, shape[i])
            if isinstance(index, np.ndarray):
                index = ensure_integer_index_array(index, shape[i])
                if i != 0:
                    raise IndexError("Indexing with lists or arrays is only supported in the first dimension")
                if len(index.shape) == 0:
                    j = int(index) # scalar index stored as a 0-d array
                    self.keys.append(slice(j, j+1, 1))
                    self.mask[i] = False
                elif len(index.shape) == 1:
                    self.keys.append(index) # array of indexes
                else:
                    raise IndexError("Indexing with multi-dimensional arrays is not supported")
            elif isinstance(index, slice):
                # Index is a slice object. Expand out any Nones in it.
                self.keys.append(slice(*index.indices(shape[i])))
            elif is_integer(index):
                # Index is a built in or numpy scalar integer
                j = int(index)
                self.keys.append(slice(j, j+1, 1))
                self.mask[i] = False
            else:
                raise IndexError("Indexes must be integer, slice, Ellipsis or array type")

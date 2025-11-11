Advanced indexing
-----------------

Remote datasets have some limited support for indexing with lists or
arrays of integers. This is similar to numpy's "advanced indexing",
but only the index in the first dimension may be an array.

.. tip:: When a remote dataset is indexed with an array, the python
         module translates the array of indexes into a sorted list of
         contiguous dataset slices to request from the server. It then
         downloads the requested slices and and returns the elements
         in the requested order. This incurs some CPU and memory
         overhead so it's more efficient to use simple
         ``[start:stop]`` slices if possible.

Indexing with integer arrays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A remote dataset may be indexed with a list or array of integers in
the first dimension. For example, if we have a dataset of length 10,
then we can obtain the first three elements as follows::

  index = [0,1,2]
  result = dataset[index]

A numpy array can also be used this context::

  index = np.arange(3)
  result = dataset[index]

.. note:: A tuple of integers (e.g. ``(0,1,2)``) will NOT work here
          because numpy indexing assumes that tuple elements refer to
          different dimensions in a multi-dimensional array.

The particular examples above are equivalent to a simple slice::

  result = dataset[0:3]

but the values in the index array do not have to be unique or
sorted. E.g.::

  index = [5, 2, 9, 9]
  result = dataset[index]

which will return elements 5 and 2 and two copies of element 9.

In case of a multidimensional dataset, only the first index may be an
array. For example, if we have an array of N three dimensional vectors
represented by a dataset with dimensions ``[N,3]``, then we can
extract the first four vectors with::

  index = np.arange(4)
  result = dataset[index, 0:3]

but attempting to extract just the x and y components with the
following would NOT work::

  index = np.arange(2)
  result = dataset[:, index]

While the index in the first dimension is allowed to be an array,
subsequent indexes must be simple ``[start:stop]`` slices, single
integer scalars, all elements (``:``), or an Ellipsis (``...``).

Indexing with boolean arrays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An array of booleans can be used to index the first dimension of a
remote dataset. The number of elements must match the size of the
dataset in the first dimension. The array is treated as a "mask" which
specifies which elements to read: elements where the index array is
``True`` will be downloaded from the server and returned.

This is implemented by translating the boolean array into an array
containing the integer indexes of the selected elements. If the
dataset has ``N`` elements and it is indexed with a boolean array
``index``, then the elements which will be read are::

  np.arange(N, dtype=int)[index]

So, for example, if we have a one dimensional dataset of length 5 and
we only want the first 3 elements we can do this::

  index = [True, True, True, False, False]
  result = dataset[index]

As before, only the index in the first dimension may be an
array. Subsequent dimensions must be simple slices or integers.

Negative indexes
^^^^^^^^^^^^^^^^

Following python convention, negative indexes count backwards from the
end of the dataset. The last element can be referenced as index
-1. Negative values are allowed as single integer indexes, the start
and stop values in ``[start:stop]`` slices, and in integer index
arrays.

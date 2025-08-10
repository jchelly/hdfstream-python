Requesting multiple slices
--------------------------

When working with simulation data it can be useful to be able to
efficiently read multiple non-contiguous chunks of a dataset
(e.g. particles in some region of a SWIFT snapshot). Requesting each
chunk separately can be slow because a round trip to the server is
required for each one.

This module provides a mechanism to fetch multiple slices with one
http request. The :py:meth:`hdfstream.RemoteDataset.request_slices`
method takes a sequence of slice objects as input and returns a single
array with the slices concatenated along the first axis. Slice objects
can be created by indexing numpy's built in ``np.s_`` object. For
example::

  import numpy as np
  
  slices = []
  slices.append(np.s_[10:20,:])
  slices.append(np.s_[50:60,:])
  data = dataset.request_slices(slices)

This would return dataset elements with coordinates 10 to 19 and 50 to
59 in the first dimension and all elements in the second
dimension. There are some restrictions on the slices:

  * Slice starting indexes in the first dimension must be in ascending order
  * Slice indexes in dimensions other than the first must not differ between slices
  * Slices must not overlap
  * Slices can only be concatenated along the first dimension

These restrictions are imposed for efficiency: slices may only be
requested in the order in which they are stored on disk, and it must
be possible to represent the combined slices as a single ndarray.

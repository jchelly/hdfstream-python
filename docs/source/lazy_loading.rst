Lazy loading settings
---------------------

The :py:func:`hdfstream.open` function takes two parameters which
affect how HDF5 file metadata (such as object names, attributes and
dataset sizes and types) are requested from the server.

The ``max_depth`` parameter determines the recursion limit when
requesting HDF5 object metadata. If this value is greater than zero
then requesting a group from the server will also request nested
subgroups up to the specified depth limit. Accessing those subgroups
later will then not require any further http requests to be sent.

The ``max_data_size`` parameter determines whether recursive requests
for HDF5 object metadata include dataset contents inline. When a group
is requested, the contents of any datasets which are no greater than
``max_data_size`` bytes are downloaded along with the metadata. This
avoids the need to send separate http requests for small datasets, at
the cost of making the metadata request more expensive.

It's possible to see which operations result in http requests by
setting the download progress bar to always display::

  import hdfstream
  hdfstream.disable_progress(False)
  hdfstream.set_progress_delay(0.0)

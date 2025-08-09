Opening files
-------------

Files can be opened by indexing a directory which contains the file::

    remote_dir = hdfstream.open("https://localhost:8443/hdfstream", "/")
    remote_file = remote_dir["path/to/file.hdf5"]

or we can open a file directly with the :py:func:`hdfstream.open` function::

    remote_file = hdfstream.open("https://localhost:8443/hdfstream", "/path/to/file.hdf5")
  
When accessing many files it's better to open the parent directory
because then file and directory metadata can be cached in the top
level directory object. This reduces the number of requests to the
server.

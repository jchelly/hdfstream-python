Accessing directories
---------------------

Directories on the server are represented by
:py:class:`hdfstream.RemoteDirectory` objects, which act like a dictionary
containing files and directories. We can request a directory from the
server and list its contents as follows::

  remote_dir = hdfstream.open("https://localhost:8443/hdfstream", "/")
  print(list(remote_dir))

We can list just the files in the directory with the ``files`` property::

  print(remote_dir.files)

and list just the directories with the ``directories`` property::

  print(remote_dir.directories)

Files and sub-directories can be opened by subscripting the directory
with the relative path of the file or directory we're interested
in. E.g. we can use::

  subsubdir = remote_dir["subdir_name/subsubdir_name"]

to access a nested directory, or we can open a file with::

  h5file = remote_dir["subdir_name/file_name.hdf5"]

which returns a :py:class:`hdfstream.RemoteFile` object.

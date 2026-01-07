#!/bin/env python

import contextlib
import h5py
import hdfstream
import numpy as np


class LocalOrRemoteFile:
    """
    Mixin class used to open local or remote files.

    This is intended to help with implementing classes which can read
    from local HDF5 files or from a hdfstream server. Classes
    which inherit from this should call :meth:`LocalOrRemoteFile.set_directory`
    in their ``__init__`` method to specify where files should be read from.
    Set the ``remote_dir`` parameter to ``None`` to read local HDF5 files.
    Set it to a :class:`hdfstream.RemoteDirectory` instance to read from a
    remote server.

    Class methods can then open files as follows::

      with self.open_file(filename) as f:
        # read from file f here

    If ``remote_dir`` was set to a remote directory, then the filename is taken
    to be relative to that directory.
    """
    def set_directory(self, remote_dir=None):
        """
        Specify where to read files from.

        :param remote_dir: The remote directory to read from, if any
        :type remote_dir: hdfstream.RemoteDirectory or None
        """
        self._remote_dir = remote_dir

    def open_direct(self, filename):
        """
        Open the specified file and return a file object.

        :param filename: The name of the file to open
        :type filename: str

        :rtype: h5py.File or hdfstream.RemoteFile
        """
        if getattr(self, "_remote_dir", None) is None:
            return h5py.File(filename, "r")
        else:
            return self._remote_dir[filename]

    @contextlib.contextmanager
    def open_file(self, filename):
        """
        Context manager used to open local or remote files.

        :param filename: Name of the file to open.
        :type filename: str
        :yields: A file object opened for reading.
        :rtype: h5py.File or hdfstream.RemoteFile
        """
        with self.open_direct(filename) as f:
            yield f

#!/bin/env python

import collections.abc
from hdfstream.remote_group import RemoteGroup
from hdfstream.defaults import *
from hdfstream.exceptions import *


class RemoteFile(collections.abc.Mapping):
    """
    This class represents a file on the server. To open a remote file, call
    hdfstream.open() with the full virtual path or index the parent
    RemoteDirectory object. The class constructor documented here is used to
    implement lazy loading of file metadata and should not usually be called
    directly.

    Indexing a RemoteFile with a HDF5 object name will yield a RemoteGroup or
    RemoteDataset object, if the file is a HDF5 file.
    
    :type connection: hdfstream.connection.Connection
    :param connection: connection object which stores http session information
    :param file_path: virtual path of the file
    :type file_path: String
    :param max_depth: maximum recursion depth for group metadata requests
    :type max_depth: int, optional
    :param data_size_limit: max. dataset size (bytes) to be downloaded with metadata
    :type data_size_limit: int, optional
    :param data: decoded msgpack data describing the file, defaults to None
    :type data: dict, optional
    """
    def __init__(self, connection, file_path, max_depth=max_depth_default,
                 data_size_limit=data_size_limit_default, data=None):

        self.connection = connection
        self.file_path = file_path
        self.max_depth = max_depth
        self.data_size_limit = data_size_limit
        self.unpacked = False

        # If msgpack data was supplied, decode it. If not, we'll wait until
        # we actually need the data before we request it from the server.
        if data is not None:
            self._unpack(data)

        self._root = None

    def _load(self):
        """
        Request the msgpack representation of this file from the server
        """
        if not self.unpacked:
            data = self.connection.request_path(self.file_path)
            self._unpack(data)

    def _unpack(self, data):
        """
        Decode the msgpack representation of this group
        """
        self.media_type = str(data["type"])
        self.size = int(data["size"])
        self.last_modified = int(data["last_modified"])
        self.unpacked = True

    @property
    def root(self):
        """
        Return a RemoteGroup corresponding to this file's HDF5 root group

        :rtype: hdfstream.RemoteGroup
        """
        if self._root is None:
            self._load()
            if self.media_type != "application/x-hdf5":
                raise HDFStreamRequestError("Cannot open non-HDF5 file as HDF5!")
            self._root = RemoteGroup(self.connection, self.file_path, name="/",
                                     max_depth=self.max_depth,
                                     data_size_limit=self.data_size_limit)
        return self._root

    def open(self, mode='r'):
        """
        Return a File-like object with the contents of the file. This can be
        used to access non-HDF5 files.

        :param mode: open the file in binary ('rb') or text ('r') mode
        :type mode: String

        :rtype: requests.Response.raw
        """
        return self.connection.open_file(self.file_path, mode=mode)

    def __getitem__(self, key):
        return self.root.__getitem__(key)

    def __len__(self):
        return self.root.__len__()

    def __iter__(self):
        for member in self.root:
            yield member

    def __repr__(self):
        return f'<Remote file "{self.file_path}">'

    def is_hdf5(self):
        """
        Return True if this is a HDF5 file, False otherwise

        :rtype: bool
        """
        self._load()
        return self.media_type == "application/x-hdf5"

    @property
    def parent(self):
        """
        For RemoteFile objects, the parent property returns the root HDF5 group

        :rtype: hdfstream.RemoteGroup
        """
        return self.root

    def _ipython_key_completions_(self):
        self._load()
        return list(self.root.keys())

    def visit(self, func):
        """
        Recursively call func on all HDF5 objects in the file. The
        function should take a single parameter which is the name of
        the visited object. If the function returns a value other than
        None then iteration stops and the value is returned.

        :param func: The function to call
        :type func: callable func(name)

        :rtype: returns the value returned by func
        """
        return self.root.visit(func)

    def visititems(self, func):
        """
        Recursively call func on all HDF5 objects in the file. The
        function should take two parameters: the name of the visited object
        and the object itself. If the function returns a value other than
        None then iteration stops and the value is returned.

        :param func: The function to call
        :type func: callable func(name, object)

        :rtype: returns the value returned by func
        """
        return self.root.visititems(func)

    def __enter__(self):
        """
        Using a RemoteFile in a with statement returns the root HDF5 group
        """
        return self.root

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        There's no cleanup to do on leaving a with statement
        """
        return False

    def close(self):
        """
        Close the file. Only included for compatibility (there's nothing to close.)
        """
        pass


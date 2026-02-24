#!/bin/env python

import collections.abc

from hdfstream.connection import Connection
from hdfstream.remote_file import RemoteFile
from hdfstream.remote_group import RemoteGroup
from hdfstream.remote_dataset import RemoteDataset
from hdfstream.defaults import *
from hdfstream.exceptions import HDFStreamRequestError


def _path_components(path):
    return [c for c in path.split("/") if c]


def _split_path(path):
    """
    Split a path into a prefix and remainder on the first slash.
    Leading and trailing slashes are ignored and consecutive slashes are
    treated as one.
    """
    components = _path_components(path)
    if len(components) > 1:
        prefix = components[0]
        remainder = "/".join(components[1:])
    else:
        prefix = None
        remainder = components[0]
    return prefix, remainder


class RemoteDirectory(collections.abc.Mapping):
    """
    This class represents a virtual directory on the server. To open a remote
    directory, call hdfstream.open() with the required path or index the parent
    RemoteDirectory with a relative path. The class constructor documented here
    is used to implement lazy loading of directory information and should not
    usually be called directly.

    Indexing a RemoteDirectory with a relative path yields another
    RemoteDirectory or a RemoteFile.

    :param server: URL of the server
    :type server: str
    :param name: virtual path of the directory to open, defaults to "/"
    :type name: str
    :param user: name of the user account for login, defaults to None
    :type user: str, optional
    :param password: password for login, defaults to None
    :type password: str, optional
    :param data: decoded msgpack data describing the directory, defaults to None
    :type data: dict, optional
    :param max_depth: maximum recursion depth for group metadata requests
    :type max_depth: int, optional
    :param data_size_limit: max. dataset size (bytes) to be downloaded with metadata
    :type data_size_limit: int, optional
    :param lazy_load: directory listing is requested immediately if False, or delayed until needed if True
    :type lazy_load: bool, optional
    :param connection: connection object which stores http session information
    :type connection: hdfstream.connection.Connection
    """
    def __init__(self, server, name="/", user=None, password=None, data=None,
                 max_depth=max_depth_default, data_size_limit=data_size_limit_default,
                 lazy_load=False, connection=None):

        # Remove any trailing slashes from the directory name
        name = name.rstrip("/")

        # Set up a new session if necessary. May need to ask for password.
        if connection is None:
            connection = Connection.new(server, user, password)
        self.connection = connection

        # Store parameters
        self.data_size_limit = data_size_limit
        self.max_depth = max_depth
        self.name = name
        self.unpacked = False
        self._files = {}
        self._directories = {}

        # If msgpack data was supplied, decode it. If not, we'll wait until
        # we actually need the data before we request it from the server.
        if data is not None:
            self._unpack(data)

        # If the class was explicitly instantiated by the user (and not by a
        # recursive _unpack() call) then we should always contact the server so
        # that we immediately detect incorrect paths.
        if lazy_load==False and not(self.unpacked):
            self._load()

    def _load(self):
        """
        Request the msgpack representation of this directory from the server
        """
        if not self.unpacked:
            data = self.connection.request_path(self.name)
            self._unpack(data)

    def _unpack(self, data):
        """
        Decode the msgpack representation of this directory
        """
        # Store directory size
        self._size = int(data["size"])

        # Store dict of files in this directory
        for filename, filedata in data["files"].items():
            file_path = self.name + "/" + filename
            if filename not in self._files:
                self._files[filename] = RemoteFile(self.connection, file_path, max_depth=self.max_depth,
                                                   data_size_limit=self.data_size_limit, data=filedata)

        # Store dict of subdirectories in this directory
        for subdir_name, subdir_data in data["directories"].items():
            if subdir_name not in self._directories:
                # This subdirectory object doesn't exist yet
                subdir_object = RemoteDirectory(self.connection.server, self.name+"/"+subdir_name, data=subdir_data,
                                                lazy_load=True, connection=self.connection, max_depth=self.max_depth,
                                                data_size_limit=self.data_size_limit)
                self._directories[subdir_name] = subdir_object
            else:
                subdir_object = self._directories[subdir_name]
                if not(subdir_object.unpacked):
                    # Directory exists but it's contents have not have been
                    # requested from the server until now.
                    assert subdir_data is None # assume we don't use recursive directory requests (i.e. max_depth=0 always)
                    subdir_object._load()
        self.unpacked = True

    def __getitem__(self, key):

        # Ensure path is a string, and not a pathlib.Path, for example
        key = str(key)

        # Split into prefix before first slash and remainder of path
        prefix, name = _split_path(key)

        # Check for the case where key refers to something in a sub-directory, sub-sub directory etc.
        # If a direct request for the target path succeeds we can infer the existence of the
        # intermediate directories and avoid loading them until we need a full directory listing.
        if prefix is not None:
            if prefix not in self._directories:
                # Request the required file or directory object data
                try:
                    data = self.connection.request_path(self.name+"/"+key)
                except HDFStreamRequestError:
                    raise KeyError(f"Invalid path: {key}")
                # Create any intermediate directory objects and set them to lazy load
                dir_obj = self
                components = _path_components(key)
                for component in components[:-1]:
                    if component not in dir_obj._directories:
                        subdir_obj = RemoteDirectory(self.connection.server, dir_obj.name+"/"+component,
                                                     lazy_load=True, connection=self.connection, max_depth=self.max_depth,
                                                     data_size_limit=self.data_size_limit)
                        dir_obj._directories[component] = subdir_obj
                        dir_obj = subdir_obj
                # Create the target object, which might be a file or directory
                if "directories" in data:
                    # It's a directory
                    dir_obj._directories[components[-1]] = RemoteDirectory(self.connection.server, dir_obj.name+"/"+components[-1], data=data,
                                                                           lazy_load=False, connection=self.connection, max_depth=self.max_depth,
                                                                           data_size_limit=self.data_size_limit)
                else:
                    # It's a file
                    dir_obj._files[components[-1]] = RemoteFile(self.connection, dir_obj.name+"/"+components[-1],
                                                                max_depth=self.max_depth, data_size_limit=self.data_size_limit,
                                                                data=data)
            return self._directories[prefix][name]

        # If we don't have this directory entry already, request the directory listing
        if name not in self._directories and name not in self._files:
            self._load()

        # Check if key refers to a subdirectory in this directory
        if name in self._directories:
            return self._directories[name]

        # Check if key refers to a file in this directory
        if name in self._files:
            return self._files[name]

        raise KeyError("Invalid path: "+key)

    def __len__(self):
        self._load()
        return len(self._directories) + len(self._files)

    def __iter__(self):
        self._load()
        for directory in self._directories:
            yield directory
        for file in self._files:
            yield file

    def __repr__(self):
        self._load()
        nr_files = len(self._files)
        nr_dirs = len(self._directories)
        return f'<Remote directory {self.name} with {nr_dirs} sub-directories, {nr_files} files>'

    @property
    def files(self):
        """
        Return a {name : RemoteFile} dict of files in this directory

        :rtype: dict
        """
        self._load()
        return self._files

    @property
    def directories(self):
        """
        Return a {name : RemoteDirectory} dict of sub-directories in this directory

        :rtype: dict
        """
        self._load()
        return self._directories

    @property
    def size(self):
        """
        Return the size of this directory's contents in bytes

        :rtype: int
        """
        self._load()
        return self._size

    @property
    def filename(self):
        """
        Return the full path to this remote directory

        :rtype: str
        """
        return self.name

    def _ipython_key_completions_(self):
        self._load()
        return list(self._directories.keys()) + list(self._files.keys())

    def File(self, filename, mode="r"):
        """
        Open the file at the specified path relative to this directory. The
        mode parameter is present for compatibility with h5py. Only mode="r"
        is accepted.

        :param filename: path of the file to open
        :type filename: str
        :param mode: mode to open the file, defaults to "r"
        :type mode: str

        :rtype: hdfstream.RemoteFile
        """
        # Locate the file
        f = self[filename]

        # Check that it really is a file
        if not isinstance(f, RemoteFile):
            raise IOError(f"Path {filename} is not a file!")

        # Check that it's a HDF5 file
        if not f.is_hdf5():
            raise IOError(f"Path {filename} is not a HDF5 file!")

        return f

    def is_hdf5(self, filename):
        """
        Return True if the specified file is a HDF5 file, False otherwise

        :param filename: name of the file to check
        :type filename: str

        :rtype: bool
        """
        # Locate the file
        try:
            f = self[filename]
        except KeyError:
            return False

        # Check that it really is a file and not a directory
        if not isinstance(f, RemoteFile):
            return False

        return f.is_hdf5()

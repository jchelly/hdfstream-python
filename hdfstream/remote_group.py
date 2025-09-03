#!/bin/env python

import collections.abc
from hdfstream.remote_dataset import RemoteDataset
from hdfstream.defaults import *
from hdfstream.soft_link import SoftLink


def _unpack_object(connection, file_path, name, data, max_depth, data_size_limit, parent):
    """
    Construct an appropriate class instance for a HDF5 object
    """
    object_type = data["hdf5_object"]
    if object_type == "group":
        return RemoteGroup(connection, file_path, name, max_depth, data_size_limit, data, parent)
    elif object_type == "dataset":
        return RemoteDataset(connection, file_path, name, data, parent)
    elif object_type == "soft_link":
        return SoftLink(data)
    else:
        raise RuntimeError("Unrecognised object type")


class RemoteGroup(collections.abc.Mapping):
    """
    This class represents a HDF5 group in a file on the server. To open a
    group, index the parent RemoteFile object. The class constructor documented
    here is used to implement lazy loading of HDF5 metadata and should not
    usually be called directly.

    Indexing a RemoteGroup with a HDF5 object name yields a RemoteGroup or
    RemoteDataset object.

    :type connection: hdfstream.connection.Connection
    :param connection: connection object which stores http session information
    :param file_path: virtual path of the file containing the group
    :type file_path: str
    :param name: name of the HDF5 group
    :type name: str
    :param max_depth: maximum recursion depth for group metadata requests
    :type max_depth: int, optional
    :param data_size_limit: max. dataset size (bytes) to be downloaded with metadata
    :type data_size_limit: int, optional
    :param data: decoded msgpack data describing the group, defaults to None
    :type data: dict, optional
    :param parent: parent HDF5 group, defaults to None
    :type parent: hdfstream.RemoteGroup, optional
    """
    def __init__(self, connection, file_path, name, max_depth=max_depth_default,
                 data_size_limit=data_size_limit_default, data=None, parent=None):

        self.connection = connection
        self.file_path = file_path
        self.name = name
        self.max_depth = max_depth
        self.data_size_limit = data_size_limit
        self.unpacked = False
        self._parent = parent

        # If msgpack data was supplied, decode it. If not, we'll wait until
        # we actually need the data before we request it from the server.
        if data is not None:
            self._unpack(data)

    def _load(self):
        """
        Request the msgpack representation of this group from the server
        """
        if not self.unpacked:
            data = self.connection.request_object(self.file_path, self.name, self.data_size_limit, self.max_depth)
            self._unpack(data)

    def _unpack(self, data):
        """
        Decode the msgpack representation of this group
        """
        # Store any attributes
        self.attrs = data["attributes"]

        # Will return zero dimensional attributes as numpy scalars
        for name, arr in self.attrs.items():
            if hasattr(arr, "shape") and len(arr.shape) == 0:
                self.attrs[name] = arr[()]

        # Create sub-objects
        self.members = {}
        if "members" in data:
            for member_name, member_data in data["members"].items():
                if member_data is not None:
                    if self.name == "/":
                        path = self.name + member_name
                    else:
                        path = self.name + "/" + member_name
                    self.members[member_name] = _unpack_object(self.connection, self.file_path, path,
                                                               member_data, self.max_depth, self.data_size_limit,
                                                               self)
                else:
                    self.members[member_name] = None

        self.unpacked = True

    def _ensure_member_loaded(self, key):
        """
        Load sub-groups on access, if they were not already loaded
        """
        self._load()
        if self.members[key] is None:
            object_name = self.name+"/"+key
            self.members[key] = RemoteGroup(self.connection, self.file_path, object_name, self.max_depth, self.data_size_limit, parent=self)

    def __getitem__(self, key):
        """
        Return a member object identified by its name or relative path.

        If the key is a path with multiple components we use the first
        component to identify a member object to pass the rest of the path to.
        """
        self._load()

        # Absolute paths need special treatment.
        if key.startswith("/"):
            if self.name != "/":
                # Currently we can't handle passing absolute paths to sub-groups
                # (h5py interprets absolute paths relative to the file's root group).
                raise NotImplementedError("Passing an absolute path to a sub-group is not implemented")
            elif key == "/":
                # If the requested path is just "/" and this is the root, return this group
                return self
            else:
                # We can just ignore leading slashes in other paths if this is the root group
                key = key.lstrip("/")

        # Split the path into first component (which identifies a member of this group) and rest of path
        components = key.split("/", 1)
        member_name = components[0]
        if len(components) > 1:
            rest_of_path = components[1].lstrip("/") # ignore any extra consecutive slashes
        else:
            rest_of_path = None

        # Locate the specifed sub group/dataset
        self._ensure_member_loaded(member_name)
        member_object = self.members[member_name]

        if rest_of_path is None:
            # No separator in key, so path specifies a member of this group
            return member_object
        else:
            # Path is a member of a member group
            if isinstance(member_object, RemoteGroup):
                if len(rest_of_path) > 0:
                    return member_object[rest_of_path]
                else:
                    # Handle case where path to group ends in a slash
                    return member_object
            else:
                raise KeyError(f"Path component {components[0]} is not a group")

    def __len__(self):
        self._load()
        return len(self.members)

    def __iter__(self):
        self._load()
        for member in self.members:
            yield member

    def __repr__(self):
        if self.unpacked:
            return f'<Remote HDF5 group "{self.name}" ({len(self.members)} members)>'
        else:
            return f'<Remote HDF5 group "{self.name}" (to be loaded on access)>'

    @property
    def parent(self):
        """
        Return the parent group of this group

        :rtype: hdfstream.RemoteGroup
        """
        if self.name == "/":
            return self
        else:
            return self._parent

    def _ipython_key_completions_(self):
        self._load()
        return list(self.members.keys())

    def _visit(self, func, path):

        for name, obj in self.items():

            if path is None:
                full_name = name
            else:
                full_name = path + "/" + name

            # Call the function on this member
            value = func(full_name)
            if value is not None:
                return value

            # If the member is a group, visit it
            if isinstance(obj, RemoteGroup):
                value = obj._visit(func, path=full_name)
                if value is not None:
                    return value

    def visit(self, func):
        """
        Recursively call func on all members of this HDF5 group. The
        function should take a single parameter which is the name of
        the visited object. If the function returns a value other than
        None then iteration stops and the value is returned.

        :param func: The function to call
        :type func: callable func(name)

        :rtype: returns the value returned by func
        """
        return self._visit(func, None)

    def _visititems(self, func, path):

        for name, obj in self.items():

            if path is None:
                full_name = name
            else:
                full_name = path + "/" + name

            # Call the function on this member
            value = func(full_name, obj)
            if value is not None:
                return value

            # If the member is a group, visit it
            if isinstance(obj, RemoteGroup):
                value = obj._visititems(func, path=full_name)
                if value is not None:
                    return value

    def visititems(self, func):
        """
        Recursively call func on all members of this HDF5 group. The
        function should take two parameters: the name of the visited object
        and the object itself. If the function returns a value other than
        None then iteration stops and the value is returned.

        :param func: The function to call
        :type func: callable func(name, object)

        :rtype: returns the value returned by func
        """
        return self._visititems(func, None)

    def close(self):
        """
        Close the group. Only included for compatibility (there's nothing to close.)
        """
        pass

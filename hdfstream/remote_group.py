#!/bin/env python

import collections.abc
from hdfstream.remote_dataset import RemoteDataset
from hdfstream.defaults import *


def unpack_object(connection, file_path, name, data, max_depth, data_size_limit, parent):
    """
    Construct an appropriate class instance for a HDF5 object
    """
    object_type = data["hdf5_object"]
    if object_type == "group":
        return RemoteGroup(connection, file_path, name, max_depth, data_size_limit, data, parent)
    elif object_type == "dataset":
        return RemoteDataset(connection, file_path, name, data, parent)
    else:
        raise RuntimeError("Unrecognised object type")


class RemoteGroup(collections.abc.Mapping):
    """
    Object representing a HDF5 group in the remote file

    Parameters:

    connection: Connection object to use to send requests
    file_path: path to the file containing the HDF5 group
    name: name of the HDF5 group to open
    max_depth: maximum recursion depth for requests to the server
    data_size_limit: maximum size of dataset body to download with metadata
    data: msgpack encoded group description
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
            self.unpack(data)

    def load(self):
        """
        Request the msgpack representation of this group from the server
        """
        if not self.unpacked:
            data = self.connection.request_object(self.file_path, self.name, self.data_size_limit, self.max_depth)
            self.unpack(data)

    def unpack(self, data):
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
                    self.members[member_name] = unpack_object(self.connection, self.file_path, path,
                                                              member_data, self.max_depth, self.data_size_limit,
                                                              self)
                else:
                    self.members[member_name] = None

        self.unpacked = True

    def ensure_member_loaded(self, key):
        """
        Load sub-groups on access, if they were not already loaded
        """
        self.load()
        if self.members[key] is None:
            object_name = self.name+"/"+key
            self.members[key] = RemoteGroup(self.connection, self.file_path, object_name, self.max_depth, self.data_size_limit, parent=self)

    def __getitem__(self, key):
        """
        Return a member object identified by its name or relative path.

        If the key is a path with multiple components we use the first
        component to identify a member object to pass the rest of the path to.
        """
        self.load()

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
        self.ensure_member_loaded(member_name)
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
        self.load()
        return len(self.members)

    def __iter__(self):
        self.load()
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
        """
        if self.name == "/":
            return self
        else:
            return self._parent

    def _ipython_key_completions_(self):
        self.load()
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
        Call callable func on all members recursively. Stops if return value
        is not None.

        func takes a single string parameter with the member name relative
        to this group.
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
        Call callable func on all members recursively. Stops if return value
        is not None.

        In this version func takes a second parameter which will return a
        RemoteGroup or RemoteDataset object.
        """
        return self._visititems(func, None)

    def close(self):
        """
        There's nothing to close, but some code might expect this to exist
        """
        pass

#!/bin/env python

import collections.abc
from hdfstream.remote_dataset import RemoteDataset
from hdfstream.defaults import *
from hdfstream.remote_links import HardLink, SoftLink


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

        # Keep a link to the root group
        if name == "/":
            self._root = self
        elif parent is not None:
            self._root = parent._root

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
        self._attrs = data["attributes"]

        # Will return zero dimensional attributes as numpy scalars
        for name, arr in self._attrs.items():
            if hasattr(arr, "shape") and len(arr.shape) == 0:
                self._attrs[name] = arr[()]

        # Create sub-objects
        self._members = {}
        if "members" in data:
            for member_name, member_data in data["members"].items():
                if member_data is not None:
                    if self.name == "/":
                        path = self.name + member_name
                    else:
                        path = self.name + "/" + member_name
                    self._members[member_name] = _unpack_object(self.connection, self.file_path, path,
                                                                member_data, self.max_depth, self.data_size_limit,
                                                                self)
                else:
                    self._members[member_name] = None

        self.unpacked = True

    @property
    def attrs(self):
        self._load()
        return self._attrs

    @property
    def members(self):
        self._load()
        return self._members

    def _ensure_member_loaded(self, key):
        """
        Load sub-groups on access, if they were not already loaded
        """
        if self.members[key] is None:
            object_name = self.name+"/"+key
            self.members[key] = RemoteGroup(self.connection, self.file_path, object_name, self.max_depth, self.data_size_limit, parent=self)

    def _get_member(self, key):
        """
        Ensure the specified member is loaded and return it. Does not
        dereference soft links, so this can return a SoftLink object.
        """
        self._ensure_member_loaded(key)
        return self.members[key]

    def get(self, key, getlink=False):
        """
        Return the object at the specified absolute or relative path. Can be
        used to distinguish soft links if getlink=True.

        :param key: path to the object
        :type key: str
        :param getlink: if True, returns a SoftLink or HardLink object
        :type getlink: bool
        """
        if getlink:
            return self._get_link(key)
        else:
            return self._get_path(key)

    def _get_path(self, key):
        """
        Return a member object identified by its name or path.
        Path can be relative or absolute.
        """
        if key == "/":
            return self._root
        elif key.startswith("/"):
            return self._root._get_path_relative(key.lstrip("/"))
        else:
            return self._get_path_relative(key)

    def _get_path_relative(self, key):
        """
        Return a member object identified by its name or path.
        The path must be relative to this group.
        """
        assert key.startswith("/")==False

        # Split the path into first component (which identifies a member of this group) and rest of path
        components = key.split("/", 1)
        member_name = components[0]
        if len(components) > 1:
            rest_of_path = components[1].lstrip("/") # ignore any extra consecutive slashes
        else:
            rest_of_path = None

        # Handle the special cases of "." and ".." in a path
        if member_name == ".":
            return self if rest_of_path is None else self[rest_of_path]
        elif member_name == "..":
            return self._parent if rest_of_path is None else self._parent[rest_of_path]

        # Locate the specifed sub group/dataset
        member_object = self._get_member(member_name)

        # If we've encountered a soft link, dereference it
        if isinstance(member_object, SoftLink):
            member_object = self[member_object.path]

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

    def _get_link(self, key):
        """
        Determine the link type of the specified absolute or relative path
        """
        if key == "/":
            raise RuntimeError("Can't get link type for the root group")
        elif key.startswith("/"):
            return self._root._get_link_relative(key.lstrip("/"))
        else:
            return self._get_link_relative(key)

    def _get_link_relative(self, key):
        """
        Determine the link type of the specified relative path
        """
        assert key.startswith("/")==False
        key = key.rstrip("/")

        # Determine the group where the link is located
        fields = key.rsplit("/", 1)
        if len(fields) == 1:
            # No separator, so key is the name of a member of this group
            group = self
            member = self._get_member(fields[0])
        else:
            # Have a separator, so key is something in a subgroup
            group = self[fields[0]]
            member = group._get_member(fields[1])

        # Return a link object
        if isinstance(member, SoftLink):
            return member
        else:
            return HardLink()

    def __getitem__(self, key):
        return self.get(key)

    def __len__(self):
        return len(self.members)

    def __iter__(self):
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

    def _copy_self(self, dest, name=None):
        """
        Copy this group to a local HDF5 file opened with h5py in writable
        mode. This is used to implement the .copy() method.

        :param source: The remote object to copy, or its path
        :type source: RemoteGroup, RemoteDataset or str
        :param dest: The local HDF5 file or group to copy the object to
        :type dest: h5py.File or h5py.Group
        :param name: The name of the object to create in dest
        :type name: str
        """

        # Determine the name of the group to create at the destination
        if name is None:
            name = self.name.split("/")[-1]

        # Create the new group
        output_group = dest.create_group(name)

        # Copy any attributes on the group
        for attr_name, attr_val in self.attrs.items():
            output_group.attrs[attr_name] = attr_val

        # Loop over group members
        for member_name in self.keys():

            # Get the link type for this member
            link = self.get(member_name, getlink=True)
            if isinstance(link, hdfstream.SoftLink):
                # This is a soft link, so make the same link in the output
                output_group[member_name] = h5py.SoftLink(link.path)
            else:
                # This is some other object, so ask it to copy itself
                self[member_name]._copy_self(output_group, member_name)


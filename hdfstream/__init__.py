#!/bin/env python

__all__ = ["verify_cert", "disable_progress", "set_progress_delay", "open",
           "RemoteDirectory", "RemoteFile", "RemoteGroup", "RemoteDataset",
           "SoftLink", "HardLink", "testing"]


from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("hdfstream")
except PackageNotFoundError:
    __version__ = "unknown"


from hdfstream.exceptions import HDFStreamRequestError
from hdfstream.connection import Connection, verify_cert
from hdfstream.decoding import disable_progress, set_progress_delay
from hdfstream.remote_directory import RemoteDirectory
from hdfstream.remote_file import RemoteFile
from hdfstream.remote_group import RemoteGroup
from hdfstream.remote_dataset import RemoteDataset
from hdfstream.remote_links import SoftLink, HardLink
from hdfstream.defaults import *


def open(server, name, user=None, password=None, max_depth=max_depth_default,
         data_size_limit=data_size_limit_default):
    """
    Connect to the server and return a RemoteDirectory or RemoteFile
    corresponding to the specified virtual path. If a user name is specified
    with no password, prompt for the password.

    :param server: URL of the server to connect to
    :type server: str
    :param name: path to the virtual file or directory on the server
    :type name: str
    :param user: name of the user account for login, defaults to None
    :type user: str, optional
    :param password: password for login, defaults to None
    :type password: str, optional
    :param max_depth: maximum recursion depth for group metadata requests
    :type max_depth: int, optional
    :param data_size_limit: max. dataset size (bytes) to download with metadata
    :type data_size_limit: int, optional

    :return: RemoteFile or RemoteDirectory corresponding to the requested path
    :rtype: RemoteFile or RemoteDirectory
    """
    connection = Connection.new(server, user, password)
    data = connection.request_path(name)

    if data["type"] == "directory":
        return RemoteDirectory(server, name, data=data, max_depth=max_depth,
                               data_size_limit=data_size_limit, lazy_load=False,
                               connection=connection)
    else:
        return RemoteFile(connection, name, max_depth=max_depth,
                          data_size_limit=data_size_limit, data=data)

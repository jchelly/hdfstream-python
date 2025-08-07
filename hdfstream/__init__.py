#!/bin/env python

from hdfstream.exceptions import HDFStreamRequestError
from hdfstream.connection import Connection, verify_cert
from hdfstream.decoding import disable_progress
from hdfstream.remote_directory import RemoteDirectory
from hdfstream.remote_file import RemoteFile
from hdfstream.remote_group import RemoteGroup
from hdfstream.remote_dataset import RemoteDataset
from hdfstream.defaults import *


def open(server, name, user=None, password=None, data=None,
         max_depth=max_depth_default, data_size_limit=data_size_limit_default):
    """
    Open a remote file or directory given a virtual path
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

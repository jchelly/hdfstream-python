#!/bin/env python

import os
import functools
import codecs
import warnings
import contextlib
import getpass

import requests
import msgpack
import numpy as np
import urllib3.exceptions
from requests.auth import HTTPBasicAuth

from hdfstream.exceptions import HDFStreamRequestError
from hdfstream.decoding import decode_response
from hdfstream.config import config


_verify_cert = True
def verify_cert(enable):
    """
    Disable SSL certificate validation. Should only be used for testing.

    :param enable: whether to validate the server's certificate
    :type enable: bool
    """
    global _verify_cert
    _verify_cert = enable


# Context manager to suppress certificate warnings if _verify=False
@contextlib.contextmanager
def _maybe_suppress_cert_warnings():
    if _verify_cert:
        # Certificate checking enabled, so do nothing
        yield
    else:
        # Certificate checking disabled, so silence warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
            yield


def raise_for_status(response):
    """
    Check the http response status and raise an exception if necessary

    This also extracts the error message from the response body, if
    there is one.
    """
    if not response.ok:
        if response.status_code == 401:
            # Catch case of wrong password
            raise HDFStreamRequestError("Not authorized. Incorrect username or password?")
        try:
            # Extract msgpack encoded error string from response.
            # decode_content=True is needed if the response is compressed.
            response.raw.read = functools.partial(response.raw.read, decode_content=True)
            data = msgpack.unpack(response.raw)
            message = data["error"]
        except Exception:
            # If we don't have a message from the server, let the requests
            # module generate an exception
            response.raise_for_status()
        else:
            # Raise an exception using the error message
            raise HDFStreamRequestError(message)


class Connection:
    """
    Class to store http session information and make requests
    """
    _cache = {}

    def __init__(self, server, user=None, password=None):

        # Remove any trailing slashes from the server name
        self.server = server.rstrip("/")

        # If a username is specified with no password, prompt for the password
        if user is not None and password is None:
            password = getpass.getpass()

        # Set up a session with the username and password
        self.session = requests.Session()
        if user is not None:
            self.session.auth = HTTPBasicAuth(user, password)

        # Test by fetching a root directory listing
        with _maybe_suppress_cert_warnings():
            response = self.session.get(self.server+"/msgpack/", verify=_verify_cert)
        raise_for_status(response)

    @staticmethod
    def new(server, user, password=None):

        # Check if server name is an alias
        server, user, password = config.resolve_alias(server, user, password)

        # Remove any trailing slashes from the server name
        server = server.rstrip("/")

        # Connection ID includes process ID to avoid issues when session
        # objects are reused between processes (e.g. with multiprocessing).
        connection_id = (server, user, os.getpid())

        # Open a new connection if necessary
        if connection_id not in Connection._cache:
            Connection._cache[connection_id] = Connection(server, user, password)
        return Connection._cache[connection_id]

    def get_and_unpack(self, url, params=None, desc=None):
        """
        Make a request and unpack the response
        """
        with _maybe_suppress_cert_warnings():
            with self.session.get(url, params=params, stream=True, verify=_verify_cert) as response:
                raise_for_status(response)
                data = decode_response(response, desc)
        return data

    def request_path(self, path):
        """
        Request the msgpack representation of a file or directory from the server
        """
        path = path.lstrip("/")
        url = f"{self.server}/msgpack/{path}"
        return self.get_and_unpack(url, desc=f"Path: {path}")

    def request_object(self, path, name, data_size_limit, max_depth):
        """
        Request the msgpack representation of a HDF5 object from the server
        """
        path = path.lstrip("/")
        params = {
            "object" : name,
            "data_size_limit" : data_size_limit,
            "max_depth" : max_depth
        }
        url = f"{self.server}/msgpack/{path}"
        return self.get_and_unpack(url, params, desc=f"Object: {name}")

    def request_slice(self, path, name, slice_string):
        """
        Request a dataset slice. Returns a new np.ndarray.
        """
        path = path.lstrip("/")
        params = {
            "object" : name,
            "slice"  : slice_string,
        }
        url = f"{self.server}/msgpack/{path}"
        return self.get_and_unpack(url, params, desc=f"Slice: {name}")

    def request_slice_into(self, path, name, slice_string, destination):
        """
        Request a dataset slice and read it into the supplied buffer.

        Will only work for fixed length data types.
        """
        path = path.lstrip("/")
        params = {
            "object" : name,
            "slice"  : slice_string,
        }
        url = f"{self.server}/msgpack/{path}"
        with _maybe_suppress_cert_warnings():
            with self.session.get(url, params=params, stream=True, verify=_verify_cert) as response:
                raise_for_status(response)
                decode_response(response, desc=f"Slice: {name}", destination=destination)

    def open_file(self, path, mode='r'):
        """
        Open the file at the specified virtual path
        """
        path = path.lstrip("/")
        url = f"{self.server}/download/{path}"

        with _maybe_suppress_cert_warnings():
            response = self.session.get(url, stream=True, verify=_verify_cert)
        raise_for_status(response)
        response.raw.read = functools.partial(response.raw.read, decode_content=True)
        if mode == 'rb':
            # Binary mode
            return response.raw
        elif mode == 'r':
            # Text mode, so we need to decode bytes to strings
            return codecs.getreader(response.encoding)(response.raw)
        else:
            raise ValueError("File mode must be 'r' (text) or 'rb' (binary)")


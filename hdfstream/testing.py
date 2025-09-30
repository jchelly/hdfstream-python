#!/bin/env python

import pytest
import gzip
import msgpack
from pathlib import Path

from vcr.persisters.filesystem import CassetteNotFoundError
from vcr.serialize import deserialize, serialize


class GzipMsgpackSerializer:
    """
    Gzipped msgpack serializer for use with vcrpy and pytest-recording
    """
    def serialize(self, cassette_dict):
        """
        Serialize a cassette dict to bytes

        :param cassette_dict: dict containing the data to serialize
        :type cassette_dict: dict
        :return: serialized data
        :rtype: bytes
        """
        return gzip.compress(msgpack.packb(cassette_dict))

    def deserialize(self, cassette_bytes):
        """
        Deserialize bytes to a cassette dict

        :param cassette_bytes: the data to deserialize
        :type cassette_bytes: bytes
        :return: a cassette dict
        :rtype: dict
        """
        return msgpack.unpackb(gzip.decompress(cassette_bytes))


class BinaryFilesystemPersister:
    """
    A vcrpy persister which can write binary files
    """
    @classmethod
    def load_cassette(cls, cassette_path, serializer):
        """
        Read and deserialize cassette data from a file path

        :param cassette_path: path to the file to read
        :type cassette_path: Path
        :param serializer_class: serializer class to use
        :type serializer_class: class
        :return: a cassette dict
        :rtype: dict
        """
        if isinstance(serializer, GzipMsgpackSerializer):
            mode = 'rb'
        else:
            mode = 'r'
        cassette_path = Path(cassette_path)
        if not cassette_path.is_file():
            raise CassetteNotFoundError()
        with cassette_path.open(mode=mode) as f:
            data = f.read()
        return deserialize(data, serializer)

    @staticmethod
    def save_cassette(cassette_path, cassette_dict, serializer):
        """
        Serialize cassette data and write it to a file

        :param cassette_path: path to the file to write
        :type cassette_path: Path
        :param cassette_dict: dict containing the data to write
        :type cassette_dict: dict
        :param serializer_class: serializer class to use
        :type serializer_class: class
        """
        if isinstance(serializer, GzipMsgpackSerializer):
            mode = 'wb'
        else:
            mode = 'w'
        data = serialize(cassette_dict, serializer)
        cassette_path = Path(cassette_path)
        cassette_folder = cassette_path.parent
        if not cassette_folder.exists():
            cassette_folder.mkdir(parents=True)
        with cassette_path.open(mode=mode) as f:
            f.write(data)


def pytest_recording_configure(config, vcr):
    """
    This registers the vcrpy serializer and persister used to store responses
    from the server for use in unit tests. Should be imported in conftest.py
    when using pytest.

    :param config: pytest configuration object
    :type config: _pytest.config.Config
    :param vcr: an instance of the VCR config object
    :type vcr: vcr.config.VCR
    """
    vcr.register_serializer('msgpack.gz', GzipMsgpackSerializer())
    vcr.register_persister(BinaryFilesystemPersister)


@pytest.fixture(scope="session")
def vcr_config():
    """
    Configure vcrpy to use the gzipped messagepack serializer. Should be
    imported in conftest.py when using pytest. Also strip out auth headers
    in case we accidentally record an authenticated request.
    """
    return {
        "serializer": "msgpack.gz",
        "filter_headers": [("authorization", "DUMMY")],
    }

class KeyringNotAvailableError(Exception):
    pass

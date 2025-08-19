#!/bin/env python

import pytest
import gzip
import yaml
from pathlib import Path

from vcr.persisters.filesystem import CassetteNotFoundError
from vcr.serialize import deserialize, serialize

class GzipYamlSerializer:
    def serialize(self, cassette_dict):
        return gzip.compress(yaml.dump(cassette_dict, Dumper=yaml.Dumper).encode())

    def deserialize(self, cassette_bytes):
        return yaml.load(gzip.decompress(cassette_bytes).decode(), Loader=yaml.Loader)

class BinaryFilesystemPersister:
    @classmethod
    def load_cassette(cls, cassette_path, serializer):
        if isinstance(serializer, GzipYamlSerializer):
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
        if isinstance(serializer, GzipYamlSerializer):
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
    vcr.register_serializer('yml.gz', GzipYamlSerializer())
    vcr.register_persister(BinaryFilesystemPersister)

@pytest.fixture(scope="session")
def vcr_config():
    return {"serializer": "yml.gz"}

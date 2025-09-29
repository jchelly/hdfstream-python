#!/bin/env python

import pytest
import keyring
import hdfstream
from hdfstream.testing import pytest_recording_configure, vcr_config, KeyringNotAvailableError
from hdfstream.config import Config

def pytest_addoption(parser):
    parser.addoption(
        "--no-verify-cert", action="store_true", default=False, help="Don't verify SSL certificates if set"
    )
    parser.addoption(
        "--server", default="https://localhost:8444/hdfstream", help="Server URL for the test"
    )

@pytest.fixture(scope='module')
def server_url(request):
    hdfstream.verify_cert(not request.config.getoption("--no-verify-cert"))
    return request.config.getoption("--server")

def open_file(server_url, filename):
    root = hdfstream.open(server_url, "/", data_size_limit=0)
    return root[filename]

@pytest.fixture(scope='module')
def eagle_snap_file(server_url):
    filename = "EAGLE/Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"
    return lambda: open_file(server_url, filename)

@pytest.fixture(scope='module')
def swift_snap_file(server_url):
    filename="Tests/SWIFT/IOExamples/ssio_ci_04_2025/EagleSingle.hdf5"
    return lambda: open_file(server_url, filename)

def raise_keyring_error(*args, **kwargs):
    raise KeyringNotAvailableError("Tests should not be using the keyring!")

@pytest.fixture(autouse=True)
def break_keyring(monkeypatch):
    monkeypatch.setattr(keyring, "get_password", raise_keyring_error)
    monkeypatch.setattr(keyring, "set_password", raise_keyring_error)

def get_test_config():
    config = Config()
    config.add_alias("example", "https://example.com/hdfstream")
    return config

@pytest.fixture(autouse=True)
def use_test_config(monkeypatch):
    monkeypatch.setattr(hdfstream.config, "get_config", get_test_config)

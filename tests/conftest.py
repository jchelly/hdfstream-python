#!/bin/env python

import pytest
from hdfstream.testing import pytest_recording_configure, vcr_config

@pytest.fixture
def server_url():
    return "https://localhost:8444/hdfstream"

@pytest.fixture
def eagle_snap_file(server_url):
    root = hdfstream.open(server_url, "/", data_size_limit=0)
    filename="EAGLE/Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"
    return root[filename]

@pytest.fixture
def swift_snap_file(server_url):
    """
    Open a SWIFT snapshot which contains soft links
    """
    import hdfstream
    root = hdfstream.open(server_url, "/", data_size_limit=0, max_depth=0)
    filename="Tests/SWIFT/IOExamples/ssio_ci_04_2025/EagleSingle.hdf5"
    return root[filename]

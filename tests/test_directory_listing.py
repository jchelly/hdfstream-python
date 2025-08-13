#!/bin/env python

import responses
import gzip
import pickle
import pytest

# Files with dummy http response data
filenames = [
    "root_listing.dat.gz",
    "EAGLE_dir_listing.dat.gz",
    "EAGLE_FM_dir_listing.dat.gz",
    "EAGLE_snap_listing.dat.gz",
    ]

# Read files and set up as responses
response_data = []
for filename in filenames:
    with gzip.open("./tests/data/responses/"+filename, "rb") as f:
        response_data.append(pickle.load(f))

@pytest.fixture
def mock_api():
    with responses.RequestsMock() as rsps:
        for data in response_data:
            responses.add(**data)
        yield rsps

@responses.activate
def test_root_listing(mock_api):

    import hdfstream
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/")
    assert len(root) == 2
    assert "EAGLE" in root
    assert "SWIFT" in root
    assert len(root.files) == 0
    assert len(root.directories) == 2

@responses.activate
def test_eagle_dir_listing(mock_api):

    import hdfstream
    eagle_dir = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/EAGLE")
    fm_dir = eagle_dir["Fiducial_models"]
    assert len(fm_dir) == 9
    expected_files = set(["description.md", "labels.msgpack"])
    assert set(fm_dir.files.keys()) == expected_files
    for name in fm_dir.files:
        assert isinstance(fm_dir[name], hdfstream.RemoteFile)
    expected_dirs = set(["RefL0012N0188", "RefL0025N0376", "RefL0025N0752", "RecalL0025N0752",
                         "RefL0050N0752", "AGNdT9L0050N0752", "RefL0100N1504"])
    assert set(fm_dir.directories.keys()) == expected_dirs

@responses.activate
def test_eagle_file_listing(mock_api):

    import hdfstream
    snap_dir = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream",
                              "/EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000")
    expected_files = set([f"snap_028_z000p000.{i}.hdf5" for i in range(16)])
    assert set(snap_dir.keys()) == expected_files
    assert set(snap_dir.files.keys()) == expected_files
    for filename in expected_files:
        f = snap_dir[filename]
        assert isinstance(f, hdfstream.RemoteFile)
        assert f.is_hdf5()

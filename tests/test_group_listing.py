#!/bin/env python

import numpy as np
import responses
import gzip
import pickle
import pytest

# Files with dummy http response data
filenames = [
    "root_listing.dat.gz",
    "EAGLE_snap_listing.dat.gz",
    "EAGLE_snap_file.dat.gz",
    "EAGLE_snap_root.dat.gz",
    "EAGLE_snap_ptype1.dat.gz",
    ]

# Read files and set up as responses
response_data = []
for filename in filenames:
    with gzip.open("./tests/data/responses/"+filename, "rb") as f:
        response_data.append(pickle.load(f))

# Read snapshot data
with gzip.open("./tests/data/snapshot/eagle_snap_data.dat.gz", "rb") as f:
    snap_data = pickle.load(f)

@pytest.fixture
def mock_api():
    with responses.RequestsMock() as rsps:
        for data in response_data:
            responses.add(**data)
        yield rsps

@responses.activate
def test_root_group_listing(mock_api):

    import hdfstream
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/")

    # Open a snapshot file
    filename="EAGLE/Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"
    snap_file = root[filename]

    # Open the root HDF5 group and check its contents
    root_group = snap_file["/"]
    expected_groups = set(["Config","Constants","HashTable","Header","Parameters",
                           "PartType0","PartType1","RuntimePars","Units"])
    assert set(root_group.keys()) == expected_groups

@responses.activate
def test_parttype1_group_listing(mock_api):

    import hdfstream
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/")

    # Open a snapshot file
    filename="EAGLE/Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"
    snap_file = root[filename]

    # Open a HDF5 group and check its contents
    ptype1 = snap_file["/PartType1"]
    expected_datasets = set(["Coordinates", "GroupNumber", "ParticleIDs",
                            "SubGroupNumber", "Velocity"])
    assert set(ptype1.keys()) == expected_datasets
    for name in ptype1.keys():
        assert isinstance(ptype1[name], hdfstream.RemoteDataset)

@responses.activate
def test_group_attributes(mock_api):

    import hdfstream
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/")

    # Open a snashot file
    filename="EAGLE/Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"
    snap_file = root[filename]

    # Open a HDF5 group and check its attributes:
    # Here we compare values decoded from the mock http response to pickled
    # test data which was extracted from the snapshot with h5py.
    header = snap_file["/Header"]
    assert set(header.attrs.keys()) == set(snap_data["header"].keys())
    for name in header.attrs.keys():
        assert np.all(header.attrs[name] == snap_data["header"][name])

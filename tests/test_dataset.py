#!/bin/env python

import numpy as np
import responses
import gzip
import pickle
import pytest

# Files with dummy http response data
filenames = [
    "root_listing.dat.gz",
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
def test_dataset_attributes(mock_api):

    import hdfstream
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/")

    # Open a snashot file
    filename="EAGLE/Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"
    snap_file = root[filename]

    # Open a HDF5 dataset and check its attributes:
    # Here we compare values decoded from the mock http response to pickled
    # test data which was extracted from the snapshot with h5py.
    dataset = snap_file["/PartType1/Coordinates"]
    assert isinstance(dataset, hdfstream.RemoteDataset)
    assert len(dataset.attrs.keys()) > 0
    assert set(dataset.attrs.keys()) == set(snap_data["ptype1_pos_attrs"].keys())
    for name in dataset.attrs.keys():
        assert np.all(dataset.attrs[name] == snap_data["ptype1_pos_attrs"][name])

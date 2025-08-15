#!/bin/env python

import responses
import gzip
import pickle
import pytest

# Files with dummy http response data
filenames = [
    "EAGLE_dir_listing.dat.gz",
    "EAGLE_FM_dir_listing.dat.gz",
    "EAGLE_snap_file.dat.gz",
    "EAGLE_snap_header.dat.gz",
    "EAGLE_snap_listing.dat.gz",
    "EAGLE_snap_ptype1.dat.gz",
    "EAGLE_snap_ptype1_slice1.dat.gz",
    "EAGLE_snap_ptype1_slice2.dat.gz",
    "EAGLE_snap_ptype1_slice3.dat.gz",
    "EAGLE_snap_ptype1_multislice1.dat.gz",
    "EAGLE_snap_ptype1_multislice2.dat.gz",
    "EAGLE_snap_root.dat.gz",
    "root_listing.dat.gz",
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
def mock_responses():
    with responses.RequestsMock() as rsps:
        for data in response_data:
            responses.add(**data)
        yield rsps

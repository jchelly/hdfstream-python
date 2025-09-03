#!/bin/env python

import numpy as np
import pytest
from test_data import snap_data
from hdfstream import RemoteGroup, RemoteDataset, SoftLink

@pytest.fixture
def snap_file():
    """
    Open a SWIFT snapshot which contains soft links
    """
    import hdfstream
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/", data_size_limit=0)
    filename="Tests/SWIFT/IOExamples/ssio_ci_04_2025/EagleSingle.hdf5"
    return root[filename]

@pytest.mark.vcr
def test_dereference_link_to_group(snap_file):
    assert isinstance(snap_file["DMParticles"], RemoteGroup)

@pytest.mark.vcr
def test_dataset_via_link_path(snap_file):
    assert isinstance(snap_file["DMParticles/Coordinates"], RemoteDataset)

@pytest.mark.vcr
def test_dataset_via_link_subscript(snap_file):
    assert isinstance(snap_file["DMParticles"]["Coordinates"], RemoteDataset)

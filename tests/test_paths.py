#!/bin/env python

import numpy as np
import pytest
from test_data import snap_data
import hdfstream
from hdfstream import RemoteGroup, RemoteDataset, SoftLink

@pytest.fixture
def snap_file():
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/", data_size_limit=0)
    filename="EAGLE/Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"
    return root[filename]

@pytest.mark.vcr
def test_leading_slash(snap_file):
    assert(snap_file["PartType1"] is snap_file["/PartType1"])

@pytest.mark.vcr
def test_trailing_slash(snap_file):
    assert(snap_file["PartType1"] is snap_file["PartType1/"])

@pytest.mark.vcr
def test_leading_trailing_slash(snap_file):
    assert(snap_file["PartType1"] is snap_file["/PartType1/"])

@pytest.mark.vcr
def test_absolute_path_root(snap_file):
    assert(snap_file["PartType1"]["/"] is snap_file["/"])

@pytest.mark.vcr
def test_absolute_path_group(snap_file):
    assert(snap_file["PartType1"]["/PartType0"] is snap_file["PartType0"])

@pytest.mark.vcr
def test_parent_path_subscript(snap_file):
    assert(snap_file["PartType1"][".."] is snap_file["/"])

@pytest.mark.vcr
def test_parent_path_append(snap_file):
    assert(snap_file["PartType1/.."] is snap_file["/"])

@pytest.mark.vcr
def test_dot_path_subscript(snap_file):
    assert(snap_file["PartType1"]["."] is snap_file["PartType1"])

@pytest.mark.vcr
def test_dot_path_append(snap_file):
    assert(snap_file["PartType1/."] is snap_file["PartType1"])

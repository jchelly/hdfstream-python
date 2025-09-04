#!/bin/env python

import numpy as np
import pytest
from test_data import snap_data
import hdfstream
from hdfstream import RemoteGroup, RemoteDataset, SoftLink

@pytest.mark.vcr
def test_leading_slash(eagle_snap_file):
    assert(eagle_snap_file["PartType1"] is eagle_snap_file["/PartType1"])

@pytest.mark.vcr
def test_trailing_slash(eagle_snap_file):
    assert(eagle_snap_file["PartType1"] is eagle_snap_file["PartType1/"])

@pytest.mark.vcr
def test_leading_trailing_slash(eagle_snap_file):
    assert(eagle_snap_file["PartType1"] is eagle_snap_file["/PartType1/"])

@pytest.mark.vcr
def test_absolute_path_root(eagle_snap_file):
    assert(eagle_snap_file["PartType1"]["/"] is eagle_snap_file["/"])

@pytest.mark.vcr
def test_absolute_path_group(eagle_snap_file):
    assert(eagle_snap_file["PartType1"]["/PartType0"] is eagle_snap_file["PartType0"])

@pytest.mark.vcr
def test_parent_path_subscript(eagle_snap_file):
    assert(eagle_snap_file["PartType1"][".."] is eagle_snap_file["/"])

@pytest.mark.vcr
def test_parent_path_append(eagle_snap_file):
    assert(eagle_snap_file["PartType1/.."] is eagle_snap_file["/"])

@pytest.mark.vcr
def test_dot_path_subscript(eagle_snap_file):
    assert(eagle_snap_file["PartType1"]["."] is eagle_snap_file["PartType1"])

@pytest.mark.vcr
def test_dot_path_append(eagle_snap_file):
    assert(eagle_snap_file["PartType1/."] is eagle_snap_file["PartType1"])

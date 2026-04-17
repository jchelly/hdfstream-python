#!/bin/env python

import numpy as np
import pytest
from test_data import snap_data
import hdfstream
from hdfstream import RemoteGroup, RemoteDataset

@pytest.mark.vcr
def test_relative_in_file(eagle_snap_file):
    snap = eagle_snap_file()
    assert "PartType1" in snap

@pytest.mark.vcr
def test_relative_not_in_file(eagle_snap_file):
    snap = eagle_snap_file()
    assert "not-present" not in snap

@pytest.mark.vcr
def test_absolute_in_file(eagle_snap_file):
    snap = eagle_snap_file()
    assert "/PartType1" in snap

@pytest.mark.vcr
def test_absolute_not_in_file(eagle_snap_file):
    snap = eagle_snap_file()
    assert "/not-present" not in snap

@pytest.mark.vcr
def test_root_in_file(eagle_snap_file):
    snap = eagle_snap_file()
    assert "/" in snap

@pytest.mark.vcr
def test_in_root(eagle_snap_file):
    snap = eagle_snap_file()
    assert "PartType1" in snap["/"]

@pytest.mark.vcr
def test_not_in_root(eagle_snap_file):
    snap = eagle_snap_file()
    assert "not-present" not in snap["/"]

@pytest.mark.vcr
def test_in_subgroup(eagle_snap_file):
    snap = eagle_snap_file()
    assert "PartType0/ElementAbundance/Carbon" in snap

@pytest.mark.vcr
def test_not_in_subgroup(eagle_snap_file):
    snap = eagle_snap_file()
    assert "PartType0/ElementAbundance/not-present" not in snap

@pytest.mark.vcr
def test_dotdot(eagle_snap_file):
    snap = eagle_snap_file()
    assert "PartType0/ElementAbundance/.." in snap

@pytest.mark.vcr
def test_dotdot_subgroup(eagle_snap_file):
    snap = eagle_snap_file()
    assert "PartType0/ElementAbundance/../ElementAbundance/Carbon" in snap

@pytest.mark.vcr
def test_group_dot(eagle_snap_file):
    snap = eagle_snap_file()
    assert "PartType0/ElementAbundance/." in snap

@pytest.mark.vcr
def test_dot_group(eagle_snap_file):
    snap = eagle_snap_file()
    assert "./PartType0/./ElementAbundance" in snap

@pytest.mark.vcr
def test_not_a_group(eagle_snap_file):
    snap = eagle_snap_file()
    assert "PartType0/ElementAbundance/Carbon/Silicon/Helium" not in snap

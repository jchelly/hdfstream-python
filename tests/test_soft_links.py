#!/bin/env python

import numpy as np
import pytest
from test_data import snap_data
from hdfstream import RemoteGroup, RemoteDataset, SoftLink, HardLink

@pytest.fixture
def snap_file():
    """
    Open a SWIFT snapshot which contains soft links
    """
    import hdfstream
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/", data_size_limit=0, max_depth=0)
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

@pytest.mark.vcr
def test_identify_soft_link_from_file(snap_file):
    link = snap_file.get("DMParticles", getlink=True)
    assert isinstance(link, SoftLink)
    assert link.path == "/PartType1"

@pytest.mark.vcr
def test_identify_soft_link_from_root(snap_file):
    link = snap_file["/"].get("DMParticles", getlink=True)
    assert isinstance(link, SoftLink)
    assert link.path == "/PartType1"

@pytest.mark.vcr
def test_identify_hard_link_from_file(snap_file):
    link = snap_file.get("PartType1", getlink=True)
    assert isinstance(link, HardLink)

@pytest.mark.vcr
def test_identify_hard_link_from_root(snap_file):
    link = snap_file["/"].get("PartType1", getlink=True)
    assert isinstance(link, HardLink)

@pytest.mark.vcr
def test_identify_soft_link_parent(snap_file):
    link = snap_file["PartType1"].get("../DMParticles", getlink=True)
    assert isinstance(link, SoftLink)
    assert link.path == "/PartType1"

@pytest.mark.vcr
def test_identify_soft_link_dot(snap_file):
    link = snap_file["PartType1"].get(".././DMParticles", getlink=True)
    assert isinstance(link, SoftLink)
    assert link.path == "/PartType1"

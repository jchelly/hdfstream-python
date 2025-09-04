#!/bin/env python

import numpy as np
import pytest
from test_data import snap_data
from hdfstream import RemoteGroup, RemoteDataset, SoftLink, HardLink

@pytest.mark.vcr
def test_dereference_link_to_group(swift_snap_file):
    assert isinstance(swift_snap_file["DMParticles"], RemoteGroup)

@pytest.mark.vcr
def test_dataset_via_link_path(swift_snap_file):
    assert isinstance(swift_snap_file["DMParticles/Coordinates"], RemoteDataset)

@pytest.mark.vcr
def test_dataset_via_link_subscript(swift_snap_file):
    assert isinstance(swift_snap_file["DMParticles"]["Coordinates"], RemoteDataset)

@pytest.mark.vcr
def test_identify_soft_link_from_file(swift_snap_file):
    link = swift_snap_file.get("DMParticles", getlink=True)
    assert isinstance(link, SoftLink)
    assert link.path == "/PartType1"

@pytest.mark.vcr
def test_identify_soft_link_from_root(swift_snap_file):
    link = swift_snap_file["/"].get("DMParticles", getlink=True)
    assert isinstance(link, SoftLink)
    assert link.path == "/PartType1"

@pytest.mark.vcr
def test_identify_hard_link_from_file(swift_snap_file):
    link = swift_snap_file.get("PartType1", getlink=True)
    assert isinstance(link, HardLink)

@pytest.mark.vcr
def test_identify_hard_link_from_root(swift_snap_file):
    link = swift_snap_file["/"].get("PartType1", getlink=True)
    assert isinstance(link, HardLink)

@pytest.mark.vcr
def test_identify_soft_link_parent(swift_snap_file):
    link = swift_snap_file["PartType1"].get("../DMParticles", getlink=True)
    assert isinstance(link, SoftLink)
    assert link.path == "/PartType1"

@pytest.mark.vcr
def test_identify_soft_link_dot(swift_snap_file):
    link = swift_snap_file["PartType1"].get(".././DMParticles", getlink=True)
    assert isinstance(link, SoftLink)
    assert link.path == "/PartType1"

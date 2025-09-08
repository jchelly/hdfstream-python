#!/bin/env python

import h5py
import hdfstream
import numpy as np
import pytest
from test_data import snap_data

def assert_same_attrs(obj1, obj2):
    """
    Assert that obj1 and obj2 have the same attribute names and values
    """
    attr_names = set(list(obj1.attrs.keys()) + list(obj2.attrs.keys()))
    for name in attr_names:
        assert name in obj1.attrs
        assert name in obj2.attrs
        assert np.all(obj1.attrs[name] == obj2.attrs[name])

def assert_same_dataset(dset1, dset2):
    """
    Assert that datasets dset1 and dset2 have the same attributes and contents
    """
    assert hasattr(dset1, "dtype")
    assert hasattr(dset2, "dtype")
    assert_same_attrs(dset1, dset2)
    assert np.all(dset1[...] == dset2[...])

def find_members(group):
    """
    Return a dict of {path : object} group members
    """
    result = {}
    def store_item(name, obj):
        result[name] = obj
    group.visititems(store_item)
    return result

def assert_same_members(group1, group2):
    """
    Assert that groups group1 and group2 have the same members
    """
    members1 = find_members(group1)
    members2 = find_members(group2)
    names = set(list(members1.keys()) + list(members2.keys()))
    for name in names:
        assert name in members1
        assert name in members2
        obj1 = members1[name]
        obj2 = members2[name]
        assert_same_attrs(obj1, obj2)
        # For datasets, check contents too
        assert hasattr(obj1, "dtype") == hasattr(obj2, "dtype")
        if hasattr(obj1, "dtype"):
            assert np.all(obj1[...] == obj2[...])

@pytest.mark.vcr
def test_copy_group_with_object_as_source(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy(root_group["Header"], outfile)

    # Check the file contents
    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        assert_same_members(root_group["Header"], outfile["Header"])

@pytest.mark.vcr
def test_copy_group_with_path_as_source(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy("Header", outfile)

    # Check the file contents
    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        assert_same_members(root_group["Header"], outfile["Header"])

@pytest.mark.vcr
def test_copy_group_with_name(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy("Header", outfile, name="CopyOfHeader")

    # Check the file contents
    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        assert "Header" not in outfile
        assert_same_members(root_group["Header"], outfile["CopyOfHeader"])

@pytest.mark.vcr
def test_copy_dataset_with_object_as_source(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy(root_group["Header/PartTypeNames"], outfile)

    # Check the file contents
    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        assert_same_dataset(root_group["Header/PartTypeNames"], outfile["PartTypeNames"])

@pytest.mark.vcr
def test_copy_dataset_with_path_as_source(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy("Header/PartTypeNames", outfile)

    # Check the file contents
    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        assert_same_dataset(root_group["Header/PartTypeNames"], outfile["PartTypeNames"])

@pytest.mark.vcr
def test_copy_dataset_with_name(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy("Header/PartTypeNames", outfile, name="CopyOfPartTypeNames")

    # Check the file contents
    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        assert "PartTypeNames" not in outfile
        assert_same_dataset(root_group["Header/PartTypeNames"], outfile["CopyOfPartTypeNames"])

@pytest.mark.vcr
def test_shallow_copy_group(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy(root_group["SubgridScheme"], outfile, shallow=True)

    # We should have copied immediate members only
    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        local_members = find_members(outfile["SubgridScheme"])
        assert set(local_members.keys()) == set(root_group["SubgridScheme"].keys())

@pytest.mark.vcr
def test_shallow_copy_root(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy(root_group, outfile, name="NewGroup", shallow=True, expand_soft=False)

    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        # We should have copied the link and not expanded it
        link = outfile["NewGroup"].get("DMParticles", getlink=True)
        assert isinstance(link, h5py.SoftLink)

@pytest.mark.vcr
def test_shallow_copy_root_expand_soft_links(swift_snap_file, tmp_path):

    # Open a snapshot file
    root_group = swift_snap_file()["/"]

    # Will copy data to a new, local, HDF5 file
    with h5py.File(tmp_path / "test_copy.hdf5", "w") as outfile:
        root_group.copy(root_group, outfile, name="NewGroup", shallow=True, expand_soft=True)

    with h5py.File(tmp_path / "test_copy.hdf5", "r") as outfile:
        # We should have expanded the link in the output
        link = outfile["NewGroup"].get("DMParticles", getlink=True)
        assert isinstance(link, h5py.HardLink)

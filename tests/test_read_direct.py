#!/bin/env python

import numpy as np
import pytest
import hdfstream

from test_data import snap_data


@pytest.fixture(scope='module')
def snap_file():
    """
    Open a snapshot file on the server
    """
    root = hdfstream.open("https://dataweb.cosma.dur.ac.uk:8443/hdfstream", "/")
    filename="EAGLE/Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"
    with root[filename] as f:
        yield f


@pytest.fixture(scope='module')
def pos_dataset(snap_file):
    dataset = snap_file["/PartType1/Coordinates"]
    assert isinstance(dataset, hdfstream.RemoteDataset)
    return dataset


@pytest.fixture(scope='module')
def vel_dataset(snap_file):
    dataset = snap_file["/PartType1/Velocity"]
    assert isinstance(dataset, hdfstream.RemoteDataset)
    return dataset


@pytest.mark.vcr
def test_read_all_pos(pos_dataset):
    """
    Try reading all particles in the test sample
    """
    expected_pos = snap_data["ptype1_pos"]
    n = expected_pos.shape[0]
    dtype = expected_pos.dtype

    pos = np.ndarray((n,3), dtype=dtype)
    pos_dataset.read_direct(pos, source_sel=np.s_[:n,:])
    assert np.all(pos[:n,:] == expected_pos)


@pytest.mark.vcr
def test_read_axis_pos(pos_dataset):
    """
    Try reading just x/y/z into a 1D array
    """
    expected_pos = snap_data["ptype1_pos"]
    n = expected_pos.shape[0]
    dtype = expected_pos.dtype

    for axis in range(3):
        pos = np.ndarray((n,), dtype=dtype)
        pos_dataset.read_direct(pos, source_sel=np.s_[:n,axis])
        assert np.all(pos==expected_pos[:,axis])


@pytest.mark.vcr
def test_read_axis_pos_into_2d(pos_dataset):
    """
    Try reading just x/y/z into part of a 2D array.
    Will fail because the destination is not contiguous.
    """
    expected_pos = snap_data["ptype1_pos"]
    n = expected_pos.shape[0]
    dtype = expected_pos.dtype

    for axis in range(3):
        pos = np.zeros((n,3), dtype=dtype)
        with pytest.raises(RuntimeError):
            pos_dataset.read_direct(pos, source_sel=np.s_[:n,axis], dest_sel=np.s_[:n,axis])


@pytest.mark.vcr
def test_read_all_pos_as_float32(pos_dataset):
    """
    Try reading float64 coords into a float32 array.
    Will fail because we would be rounding the result.
    """
    expected_pos = snap_data["ptype1_pos"]
    n = expected_pos.shape[0]
    dtype = expected_pos.dtype

    pos = np.ndarray((n,3), dtype=np.float32)
    with pytest.raises(RuntimeError):
        pos_dataset.read_direct(pos, source_sel=np.s_[:n,:])


@pytest.mark.vcr
def test_read_all_vel_as_float64(vel_dataset):
    """
    Try reading float32 velocity into a float64 array.
    Converting to a more precise type is ok.
    """
    expected_vel = snap_data["ptype1_vel"]
    n = expected_vel.shape[0]
    dtype = expected_vel.dtype

    vel = np.ndarray((n,3), dtype=np.float64)
    vel_dataset.read_direct(vel, source_sel=np.s_[:n,:])
    assert np.all(vel==expected_vel)


@pytest.mark.vcr
def test_read_partial_vel_no_conversion(vel_dataset):
    """
    Try reading a subset of velocities into a subset of the destination.
    No type conversion is done in this case.
    """
    expected_vel = snap_data["ptype1_vel"]
    n = expected_vel.shape[0]
    dtype = expected_vel.dtype

    vel = np.zeros((n,3), dtype=np.float32)
    vel_dataset.read_direct(vel, source_sel=np.s_[200:300,:], dest_sel=np.s_[200:300,:])
    assert np.all(vel[200:300,:]==expected_vel[200:300,:])


@pytest.mark.vcr
def test_read_partial_vel_with_conversion(vel_dataset):
    """
    Try reading a subset of velocities into a subset of the destination.
    Type conversion is needed, so we'll be copying the data here.
    """
    expected_vel = snap_data["ptype1_vel"]
    n = expected_vel.shape[0]
    dtype = expected_vel.dtype

    vel = np.zeros((n,3), dtype=np.float64)
    vel_dataset.read_direct(vel, source_sel=np.s_[200:300,:], dest_sel=np.s_[200:300,:])
    assert np.all(vel[200:300,:]==expected_vel[200:300,:])

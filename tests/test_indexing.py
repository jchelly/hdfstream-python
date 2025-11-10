#!/bin/env python

import numpy as np
import pytest
import hdfstream

from dummy_dataset import DummyRemoteDataset

#
# Scalar dataset tests
#
@pytest.fixture(params=[True, False])
def dset_scalar(request):
    data = np.ones((), dtype=int)
    return DummyRemoteDataset("/filename", "objectname", data, cache=request.param)

def test_scalar_empty(dset_scalar):
    assert dset_scalar[()] == 1

def test_scalar_ellipsis(dset_scalar):
    assert dset_scalar[...] == 1

def test_scalar_colon(dset_scalar):
    with pytest.raises(IndexError):
        result = dset_scalar[:]

def test_scalar_indexed(dset_scalar):
    with pytest.raises(IndexError):
        result = dset_scalar[0]

#
# 1D dataset tests
#
@pytest.fixture(params=[True, False])
def dset_1d(request):
    data = np.arange(100, dtype=int)
    return DummyRemoteDataset("/filename", "objectname", data, cache=request.param)

# Some valid slices into a 1D array
keys_1d_slices = [
    np.s_[...],
    np.s_[:],
    np.s_[0:100],
    np.s_[50:60],
    np.s_[50:60:1],
    np.s_[-50:-40],
    np.s_[0],
    np.s_[99],
    np.s_[12],
    np.s_[-12],
    np.s_[90:120], # valid because numpy truncates out of range slices
]
# Some valid lists of indexes into a 1D array
keys_1d_arrays = [
    [0,1,2,3],
    [3,2,1,0],
    [5,6,7,10,40,41,42,90,95,96,97],
    [5,6,6,6,7,10,40,41,42,90,90,95,96,97],
    [0,],
    [99,],
    [87, 32, 59, 60, 61, 68, 3],
    np.arange(100, dtype=int).tolist(),
    np.arange(100, dtype=int)[::-1].tolist(),
    [-1,],
    [-1,-2,-3],
    [4,5,6,-10,-11,-12],
    [5,5,5,5,5,5],
]
@pytest.mark.parametrize("key", keys_1d_slices + keys_1d_arrays + [np.asarray(k, dtype=int) for k in keys_1d_arrays])
def test_1d(dset_1d, key):
    expected = dset_1d.arr[key]
    actual = dset_1d[key]
    assert expected.dtype == actual.dtype
    assert expected.shape == actual.shape
    assert np.all(expected == actual)

# Some invalid slices
bad_1d_slices = [
    np.s_[0:100:2], # step != 1
    np.s_[100:0:-1],
    np.s_[200], # numpy does bounds check integer indexes
    np.s_[-200],
    np.s_[10,20], # too many dimensions
    np.s_[30:40,5],
    np.s_[5, 30:40],
]
@pytest.mark.parametrize("key", bad_1d_slices)
def test_1d_bad_slice(dset_1d, key):
    with pytest.raises(IndexError):
        result = dset_1d[key]

# Some invalid arrays of indexes. Values don't have to be sorted or unique
# so only out of bounds values are invalid.
bad_1d_arrays = [
    [98, 99, 100, 101],
    [-101, -100, -99, -98],
]
@pytest.mark.parametrize("key", bad_1d_arrays)
def test_1d_bad_array(dset_1d, key):
    with pytest.raises(IndexError):
        result = dset_1d[key]

#!/bin/env python

import numpy as np
import pytest
from itertools import product

import hdfstream
from dummy_dataset import DummyRemoteDataset

def list_to_array(l):
    """
    Convert a list of integers or booleans to an array. Need to avoid
    returning a float array if the list is empty.
    """
    if len(l) > 0:
        return np.asarray(l)
    else:
        return np.asarray(l, dtype=int)

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
# 1D dataset tests: try running these with different limits on the number of
# slices per requests, to test the chunking algorithm.
#
max_nr_slices = [1,2,3,4,8,100]
cache_data    = [True, False]
@pytest.fixture(params=list(product(cache_data, max_nr_slices)))
def dset_1d(request):
    cache_data, max_nr_slices = request.param
    data = np.arange(100, dtype=int)
    return DummyRemoteDataset("/filename", "objectname", data, cache=cache_data, max_nr_slices=max_nr_slices)

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
    [],
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
    [True,]*100,
    [False,]*100,
    [True,]*50+[False,]*50,
    [True,]*20+[False,]*50+[True,]*30,
    [False, True, True, True,]*25,
]
@pytest.mark.parametrize("key", keys_1d_slices + keys_1d_arrays + [list_to_array(k) for k in keys_1d_arrays])
def test_1d_valid(dset_1d, key):
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

#
# 2D dataset tests
#
# Test dataset is the same size as the 1D dataset but with an extra dimension
#
@pytest.fixture(params=list(product(cache_data, max_nr_slices)))
def dset_2d(request):
    cache_data, max_nr_slices = request.param
    data = np.ndarray((100,3), dtype=int)
    for i in range(3):
        data[:,i] = np.arange(100, dtype=int) + i*1000
    return DummyRemoteDataset("/filename", "objectname", data, cache=cache_data, max_nr_slices=max_nr_slices)

# The 2D test cases are the 1D test cases with various indexes in the second dimension
keys_in_second_dim = [
    np.s_[0:0],
    np.s_[...],
    np.s_[:],
    0,
    1,
    2,
    np.s_[0:3],
    np.s_[0:2],
    np.s_[1:2],
]
valid_keys_2d = list(product(keys_1d_slices+keys_1d_arrays, keys_in_second_dim))
valid_keys_2d = [k for k in valid_keys_2d if k[0] is not Ellipsis or k[1] is not Ellipsis] # discard invalid [Ellipsis, Ellipsis] case
@pytest.mark.parametrize("key", valid_keys_2d)
def test_2d_valid(dset_2d, key):
    expected = dset_2d.arr[key]
    actual = dset_2d[key]
    assert expected.dtype == actual.dtype
    assert expected.shape == actual.shape
    assert np.all(expected == actual)

# Try some 2D cases with invalid slices in the first dimension
bad_keys_2d_1 = list(product(bad_1d_slices+bad_1d_arrays, keys_in_second_dim))
@pytest.mark.parametrize("key", bad_keys_2d_1)
def test_2d_bad_slice_first_dim(dset_2d, key):
    with pytest.raises(IndexError):
        result = dset_2d[key]

# Try some 2D cases with invalid slices in the second dimension
bad_keys_in_second_dim = [
    4, # out of bounds
    -4,
    [0,3], # not a simple slice
    np.s_[0:3:2], # step is not 1
]
bad_keys_2d_2 = list(product(keys_1d_slices+keys_1d_arrays, bad_keys_in_second_dim))
@pytest.mark.parametrize("key", bad_keys_2d_2)
def test_2d_bad_slice_second_dim(dset_2d, key):
    with pytest.raises(IndexError):
        result = dset_2d[key]

# Make sure we're not allowing two Ellipsis
def test_2d_two_ellipsis(dset_2d):
    with pytest.raises(IndexError):
        result = dset_2d[...,...]

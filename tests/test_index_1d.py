#!/bin/env python

import numpy as np
import pytest
from itertools import product

import hdfstream
from dummy_dataset import DummyRemoteDataset
from utils import list_to_array, assert_arrays_equal, context_from_expectation

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

# Some valid indexes
test_cases = [
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
    np.s_[90:120],
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
    (),
    np.s_[...,0],
    np.s_[0,...],
    np.s_[...,:],
    np.s_[:,...],
    np.s_[...,20:30],
    np.s_[20:30,...],
    np.s_[[5,6,7],...],
]
# Repeat test cases where the key is a list with an equivalent array
for tc in test_cases:
    if isinstance(tc, list):
        test_cases.append(list_to_array(tc))

@pytest.mark.parametrize("key", test_cases)
def test_1d_valid(dset_1d, key):
    expected = dset_1d.arr[key]
    actual = dset_1d[key]
    assert_arrays_equal(expected, actual)

# Some invalid indexes
bad_test_cases = [
    np.s_[0:100:2], # step != 1
    np.s_[100:0:-1],
    np.s_[200], # numpy does bounds check integer indexes
    np.s_[-200],
    np.s_[10,20], # too many dimensions
    np.s_[30:40,5],
    np.s_[5, 30:40],
    [98, 99, 100, 101], # out of bounds array values
    [-101, -100, -99, -98],
    [True,]*101, # wrong size boolean mask
    [True,]*99,
    np.s_[...,[5,6,7]], # possibly should be allowed if Ellipsis represents zero dimensions?
]
@pytest.mark.parametrize("key", bad_test_cases)
def test_1d_bad_array(dset_1d, key):
    with pytest.raises(IndexError):
        result = dset_1d[key]

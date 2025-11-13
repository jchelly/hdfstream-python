#!/bin/env python

import numpy as np
import pytest
from itertools import product

import hdfstream
from dummy_dataset import DummyRemoteDataset
from utils import list_to_array, assert_arrays_equal

# 2D dataset for testing
max_nr_slices = [1,2,3,4,8,100]
cache_data    = [True, False]
@pytest.fixture(params=list(product(cache_data, max_nr_slices)))
def dset_2d(request):
    cache_data, max_nr_slices = request.param
    data = np.ndarray((100,3), dtype=int)
    for i in range(3):
        data[:,i] = np.arange(100, dtype=int) + i*1000
    return DummyRemoteDataset("/filename", "objectname", data, cache=cache_data, max_nr_slices=max_nr_slices)

# Some valid indexes into the first dimension of a 2D array
keys_2d_0 = [
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

# Some valid indexes into the second dimension of a 2D array
keys_2d_1 = [
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

# Test all combinations in first and second dimension
all_test_cases = [tc for tc in list(product(keys_2d_0, keys_2d_1)) if tc[0] is not Ellipsis or tc[1] is not Ellipsis]

# Also test using an index in the first dimension only
for tc in keys_2d_0:
    all_test_cases.append(tc)

# Add some test cases with extra Ellipsis
for tc in list(product(keys_2d_0, keys_2d_1)):
    if tc[0] is not Ellipsis and tc[1] is not Ellipsis:
        # Make a copy of this test with a trailing Ellipsis
        all_test_cases.append(tc+(Ellipsis,))
        # Make a copy of this test with an Ellipsis between dimensions
        all_test_cases.append((tc[0], Ellipsis, tc[1]))
        # Make a copy with a leading Ellipsis, if the first index is not an array or list
        if not isinstance(tc[0], (np.ndarray, list)):
            all_test_cases.append((Ellipsis,)+tc)

@pytest.mark.parametrize("key", all_test_cases)
def test_2d(dset_2d, key):
    expected = dset_2d.arr[key]
    actual = dset_2d[key]
    assert_arrays_equal(expected, actual)

# Some invalid indexes in the first dimension
bad_keys_2d_0 = [
    np.s_[0:100:2], # step != 1
    np.s_[100:0:-1],
    np.s_[200], # numpy does bounds check integer indexes
    np.s_[-200],
    np.s_[10,20], # too many dimensions
    [98, 99, 100, 101], # out of bounds array values
    [-101, -100, -99, -98],
    [True,]*101, # wrong size boolean mask
    [True,]*99,
    np.s_[...,[5,6,7]], # possibly should be allowed if Ellipsis represents zero dimensions?
]

# Some invalid indexes in the second dimension
bad_keys_2d_1 = [
    4, # out of bounds
    -4,
    [0,3], # not a simple slice
    np.s_[0:3:2], # step is not 1
]

# Test cases where the first index is invalid and the second index is valid
all_bad_test_cases = list(product(bad_keys_2d_0, keys_2d_1))

# Test cases where the first index is invalid and there is no second index
all_bad_test_cases += bad_keys_2d_0

# Test cases where both indexes are invalid
all_bad_test_cases += list(product(bad_keys_2d_0, bad_keys_2d_1))

# Test cases where the second index is invalid
all_bad_test_cases += list(product(keys_2d_0, bad_keys_2d_1))

@pytest.mark.parametrize("key", all_bad_test_cases)
def test_2d_bad(dset_2d, key):
    with pytest.raises(IndexError):
        result = dset_2d[key]

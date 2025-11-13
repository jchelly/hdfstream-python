#!/bin/env python

import numpy as np
import pytest

from dummy_dataset import DummyRemoteDataset
from utils import context_from_expectation

#
# Use .read_direct() to read scalars
#
@pytest.fixture(params=[True, False])
def dset_scalar(request):
    data = np.ones((), dtype=int)
    return DummyRemoteDataset("/filename", "objectname", data, cache=request.param)

# Indexes and expected results
test_cases = [
    [np.s_[()],                      1],
    [np.s_[...],                     1],
    [np.s_[(...,)],                  1],
    [np.s_[np.zeros((), dtype=int)], IndexError],
    [np.s_[:],                       IndexError],
    [np.s_[0],                       IndexError],
    [np.s_[np.arange(10)],           IndexError],
    [np.s_[(...,...)],               IndexError],
]

@pytest.mark.parametrize("key,expected", test_cases)
def test_direct_scalar(dset_scalar, key, expected):
    result = np.ndarray((), dtype=dset_scalar.dtype)
    with context_from_expectation(expected):
        dset_scalar.read_direct(result, key)
        assert result == expected

#
# Use read_direct() to read a 1D array
#
@pytest.fixture(params=[True, False])
def dset_1d(request):
    data = np.arange(100, dtype=int)
    return DummyRemoteDataset("/filename", "objectname", data, cache=request.param)


def test_direct_1d_slice(dset_1d):
    key = np.s_[20:30]
    result = np.ndarray(10, dtype=dset_1d.dtype)
    dset_1d.read_direct(result, key)
    assert np.all(result == dset_1d.arr[key])

def test_direct_1d_slice_with_dest_sel(dset_1d):
    key = np.s_[20:30]
    result = np.ndarray(50, dtype=dset_1d.dtype)
    sel = np.s_[15:25]
    dset_1d.read_direct(result, key, sel)
    assert np.all(result[sel] == dset_1d.arr[key])

def test_direct_1d_slice_no_tuple(dset_1d):
    key = slice(20,30)
    result = np.ndarray(10, dtype=dset_1d.dtype)
    dset_1d.read_direct(result, key)
    assert np.all(result == dset_1d.arr[key])

def test_direct_1d_integer(dset_1d):
    key = np.s_[10]
    result = np.ndarray((), dtype=dset_1d.dtype)
    dset_1d.read_direct(result, key)
    assert np.all(result == dset_1d.arr[key])

def test_direct_1d_integer_no_tuple(dset_1d):
    key = 10
    result = np.ndarray((), dtype=dset_1d.dtype)
    dset_1d.read_direct(result, key)
    assert np.all(result == dset_1d.arr[key])

def test_direct_1d_ellipsis(dset_1d):
    key = np.s_[...]
    result = np.ndarray(dset_1d.shape, dtype=dset_1d.dtype)
    dset_1d.read_direct(result, key)
    assert np.all(result == dset_1d.arr[key])

def test_direct_1d_ellipsis_no_tuple(dset_1d):
    key = Ellipsis
    result = np.ndarray(dset_1d.shape, dtype=dset_1d.dtype)
    dset_1d.read_direct(result, key)
    assert np.all(result == dset_1d.arr[key])

def test_direct_1d_colon(dset_1d):
    key = np.s_[:]
    result = np.ndarray(dset_1d.shape, dtype=dset_1d.dtype)
    dset_1d.read_direct(result, key)
    assert np.all(result == dset_1d.arr[key])

def test_direct_1d_colon_no_tuple(dset_1d):
    key = slice(None)
    result = np.ndarray(dset_1d.shape, dtype=dset_1d.dtype)
    dset_1d.read_direct(result, key)
    assert np.all(result == dset_1d.arr[key])

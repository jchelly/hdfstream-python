#!/bin/env python

import numpy as np
import pytest
import hdfstream

from dummy_dataset import DummyRemoteDataset

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

@pytest.fixture(params=[True, False])
def dset_1d(request):
    data = np.arange(100, dtype=int)
    return DummyRemoteDataset("/filename", "objectname", data, cache=request.param)

# Some valid slices into a 1D array
keys_1d = [
    np.s_[...],
    np.s_[:],
    np.s_[0:100],
    np.s_[50:60],
    np.s_[50:60:1],
    np.s_[0],
    np.s_[99],
    np.s_[12],
    np.s_[np.int32(12)],
]
@pytest.mark.parametrize("key", keys_1d)
def test_1d_ellipsis(dset_1d, key):
    expected = dset_1d.arr[key]
    actual = dset_1d[key]
    assert expected.dtype == actual.dtype
    assert expected.shape == actual.shape
    assert np.all(expected == actual)

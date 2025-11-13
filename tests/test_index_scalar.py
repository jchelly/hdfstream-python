#!/bin/env python

import numpy as np
import pytest

from dummy_dataset import DummyRemoteDataset
from utils import context_from_expectation

#
# Scalar dataset tests
#
# A scalar dataset to try indexing
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
def test_scalar(dset_scalar, key, expected):
        # Check that numpy behaves as we expect (i.e. is our expectation correct)
        with context_from_expectation(expected):
            result = dset_scalar.arr[key]
            assert result == expected
        # Check that the remote dataset behaves as we expect
        with context_from_expectation(expected):
            result = dset_scalar[key]
            assert result == expected

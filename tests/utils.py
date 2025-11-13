#!/bin/env python

import numpy as np
import pytest
import contextlib

def list_to_array(l):
    """
    Convert a list of integers or booleans to an array. Need to avoid
    returning a float array if the list is empty.
    """
    if len(l) > 0:
        return np.asarray(l)
    else:
        return np.asarray(l, dtype=int)

def assert_arrays_equal(expected, actual):
    assert expected.dtype == actual.dtype
    assert expected.shape == actual.shape
    assert np.all(expected == actual)

def context_from_expectation(expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        return pytest.raises(expected)
    else:
        return contextlib.nullcontext(expected)

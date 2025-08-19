#!/bin/env python

import gzip
import pickle

# Read snapshot data
with gzip.open("./tests/data/snapshot/eagle_snap_data.dat.gz", "rb") as f:
    snap_data = pickle.load(f)

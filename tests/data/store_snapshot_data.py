#!/bin/env python
#
# Store some data from an EAGLE snapshot for testing purposes. Will compare
# this to data decoded from mock http responses when running unit tests.
#

filename = "/cosma7/data/Eagle/DataRelease/L0012N0188/PE/REF_COSMA5/data/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"

import h5py
import pickle
import gzip

with h5py.File(filename, "r") as snap:

    n = 1000

    # Get the file header as a dict of arrays
    header_data = {}
    header = snap["Header"]
    for name in header.attrs:
        header_data[name] = header.attrs[name]

    # Read particle positions
    ptype1_pos = snap["PartType1/Coordinates"]
    ptype1_pos_data = ptype1_pos[:n,:]
    ptype1_pos_attrs = {}
    for name in ptype1_pos.attrs:
        ptype1_pos_attrs[name] = ptype1_pos.attrs[name]

    # Read particle velocities
    ptype1_vel = snap["PartType1/Velocity"]
    ptype1_vel_data = ptype1_vel[:n,:]
    ptype1_vel_attrs = {}
    for name in ptype1_vel.attrs:
        ptype1_vel_attrs[name] = ptype1_vel.attrs[name]

# Store the result
data = {
    "header" : header_data,
    "ptype1_pos" : ptype1_pos_data,
    "ptype1_pos_attrs" : ptype1_pos_attrs,
    "ptype1_vel" : ptype1_vel_data,
    "ptype1_vel_attrs" : ptype1_vel_attrs,
}

with gzip.open("snapshot/eagle_snap_data.dat.gz", "wb") as f:
    pickle.dump(data, f)

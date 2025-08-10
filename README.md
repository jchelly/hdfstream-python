# Python client module for HDF5 streaming service

This module provides facilities to access HDF5 files stored on a
remote server which streams their contents in messagepack format. It
attempts to replicate the [h5py](https://www.h5py.org/) high level
interface to some extent.

The source code and issue tracker are hosted on github:
https://github.com/jchelly/hdfstream-python

Releases are hosted on pypi: https://pypi.org/project/hdfstream/

Full documentation is in the `docs` directory and on Read the Docs.

## Installation

The module can be installed using pip:
```
pip install hdfstream
```

## Quick start

### Connecting to the server

You can connect to the server as follows:
```
import hdfstream
root = hdfstream.open("https://localhost:8443/hdfstream", "/")
```
Here, the first parameter is the server URL and the second is the name
of the directory to open. This returns a RemoteDirectory object.

### Opening a file

The RemoteDirectory behaves like a python dictionary where the keys
are the names of files and subdirectories within the directory. A file
or subdirectory can be opened by indexing the RemoteDirectory. For
example:
```
# Open a HDF5 file
snap_file = root["EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000/snap_028_z000p000.0.hdf5"]
```
which opens the specified file and returns a RemoteFile object.

### Reading datasets

We can read a dataset by indexing the file:
```
# Read all dark matter particle positions in the file
dm_pos = snap_file["PartType1/Coordinates"][...]
```
or if we only want to download part of the dataset:
```
# Read the first 100 dark matter particle positions
dm_pos = snap_file["PartType1/Coordinates"][:100,:]
```
HDF5 attributes can be accessed using the attrs field of group and dataset objects:
```
print(snap_file["Header"].attrs)
```

## Building the documentation

```
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
cd docs
make html
```

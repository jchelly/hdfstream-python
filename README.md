# Python client module for the hdfstream HDF5 streaming service

This module provides facilities to access HDF5 files stored on a
remote server which streams their contents in messagepack format. It
attempts to replicate the [h5py](https://www.h5py.org/) high level
interface to some extent.

The source code and issue tracker are hosted on github:
https://github.com/jchelly/hdfstream-python

Releases are hosted on pypi: https://pypi.org/project/hdfstream/

For documentation see: https://hdfstream-python.readthedocs.io/en/latest

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
or subdirectory can be opened by like this:
```
# Open a HDF5 file
snap_file = root["EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000/snap_028_z000p000.0.hdf5"]
```
which opens the specified file and returns a RemoteFile object.

### Reading datasets

The file object acts like a dictionary containing HDF5 groups and
datasets, so we can read a dataset as follows:
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

To make a local copy of the documentation in html format:
```
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
cd docs
make html
```

## Testing

There are some basic unit tests which can be run without access to a
server. The repository includes a few pre-recorded responses from the
server and a small amount of simulation data to check that the module
can decode responses correctly. The tests can be run by running
`pytest` in the source directory.

The scripts in `tests/data` can be used to regenerate the test data
files if necessary.

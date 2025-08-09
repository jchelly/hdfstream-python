# Python client module for HDF5 streaming service

This module provides facilities to access HDF5 files stored on a
remote server which streams their contents in messagepack format. It
attempts to replicate the [h5py](https://www.h5py.org/) high level
interface to some extent.

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

### Remote file and directory objects

The RemoteDirectory behaves like a python dictionary where the keys
are the names of files and subdirectories within the directory. We can
list the contents with:
```
print(list(root))
```
A file or subdirectory can be opened by indexing the RemoteDirectory. For example:
```
# Open a subdirectory
subdir = root["EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000"]
```
which returns another RemoteDirectory, or
```
# Open a HDF5 file
snap_file = root["EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000/snap_028_z000p000.0.hdf5"]
```
which opens the specified file and returns a RemoteFile object.

### Reading HDF5 groups and datasets

Files are opened by indexing the directory object with the path to the file:
```
snap_file = root["EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000/snap_028_z000p000.0.hdf5"]
```
This returns a RemoteFile object, which behaves like a h5py.File. We
can read a dataset by indexing the file:
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
And we can list the contents of a group:
```
print(list(snap_file["PartType0"]))
```

### Requesting multiple dataset slices

When working with simulation data it can be useful to be able to
efficiently read multiple non-contiguous chunks of a dataset
(e.g. particles in some region of a SWIFT snapshot). Requesting each
chunk separately can be slow because a round trip to the server is
required for each one.

This module provides a mechanism to fetch multiple slices with one
http request. Remote datasets have a `request_slices()` method which
takes a sequence of slice objects as input and returns a single array
with the slices concatenated along the first axis. Slice objects can
be created by indexing numpy's built in `np.s_` object. For example:
```
slices = []
slices.append(np.s_[10:20,:])
slices.append(np.s_[50:60,:])
data = dm_pos.request_slices(slices)
```
This would return the coordinates of particles 10 to 19 and 50 to 59
in a single array of shape (20,3). There are some restrictions on the
slices:
  * Slice starting indexes in the first dimension must be in ascending order
  * Slice indexes in dimensions other than the first must not differ between slices
  * Slices must not overlap
  * Slices can only concatenated along the first dimension

### Download progress indication

By default the module will show a progress bar (using
[tqdm](https://github.com/tqdm/tqdm)) during downloads if stdout is a
terminal. To prevent this:
```
import hdfstream
hdfstream.disable_progress(True)
```
Set this to False to always show the progress bar or None to restore
the default behaviour. You can also set the delay in seconds before the
progress bar is shown:
```
hdfstream.set_progress_delay(1.0)
```
Setting the delay to zero will generate output for every http request
made by the module.

#!/bin/env python

# Default maximum recursion depth when loading nested groups in a single
# request. Deeper groups are only loaded when requested.
max_depth_default = 1

# Default maximum size in bytes of dataset contents to load with the parent
# group. Larger datasets are only loaded when sliced.
data_size_limit_default = 64*1024

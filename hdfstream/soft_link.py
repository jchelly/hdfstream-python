#!/bin/env python

class SoftLink():
    """
    This class represents a soft link in a HDF5 file. It's just a container
    for a single string with the link target path.

    :param data: decoded msgpack data describing the link
    :type data: dict, optional
    """
    def __init__(self, data):

        assert data["hdf5_object"] == "soft_link"
        self.target = data["target"]

    def __repr__(self):
        return f'<Soft link to "{self.target}">'

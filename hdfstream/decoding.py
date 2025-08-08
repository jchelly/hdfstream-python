#!/bin/env python

import requests
import msgpack
import msgpack_numpy as mn
import numpy as np
from tqdm import tqdm

from hdfstream.streaming_decoder import StreamingDecoder

# Chunk size in bytes for reading http responses
chunk_size = 1024*1024

# Big endian int types used to interpret msgpack data
be_uint8  = np.dtype(">u1")
be_uint16 = np.dtype(">u2")
be_uint32 = np.dtype(">u4")


_disable_progress = None
_progress_delay = 0.1
def disable_progress(disable):
    """
    Allow enabling or disabling the progress bar. Sets tqdm(disable=...).

    True: never show
    False: always show
    None: (default) show if stdout is a terminal
    """
    global _disable_progress
    _disable_progress = disable


def set_progress_delay(delay):
    global _progress_delay
    _progress_delay = delay


def decode_hook(data):
    """
    Converts dicts decoded from the msgpack stream into numpy ndarrays. Called
    by msgpack.unpack().

    Dicts with nd=True contain a binary buffer which should be wrapped with a
    numpy array with type and shape given by the metadata in the dict. We call
    msgpack-numpy's decode() function to do this.

    Dicts with vlen=True contain flattened lists of variable size
    elements and are translated into numpy object arrays.
    """

    # If this is a serialized ndarray, use msgpack-numpy to decode it.
    # Data from the server is not quite compatible with msgpack-numpy,
    # so fix it up here.
    if isinstance(data, dict) and "nd" in data:

        # Any string keys must be converted to bytes
        result = {}
        for name in data:
            result[name.encode(encoding="ascii")] = data[name]

        # The array of buffers must be merged (in case of >4GB data).
        if b"data" in result and result[b"data"] is not None:
            result[b"data"] = b''.join(result[b"data"])

        # Decode the array and copy it to make it writable
        data = mn.decode(result).copy()

    # Then check for any vlen data: in that case we have a flattened list
    # which needs to be converted into an object array of the right shape.
    if isinstance(data, dict) and "vlen" in data:
        # Get the shape of the array
        shape = [int(i) for i in data["shape"]]
        if len(shape) == 0:
            # For scalars, just return the value
            data = data["data"][0]
        else:
            # Otherwise we make an object array
            arr = np.empty(len(data["data"]), object)
            arr[:] = data["data"]
            data = arr.reshape(shape)
    return data


def decode_response(response, desc):
    """
    Decode a msgpack encoded http response

    Peeks at the first part of the response to determine which
    decoder to use.
    """

    # Expected prefix for a fixed size binary array:
    # 6 element map header, string "nd", then boolean true.
    array_prefix = bytes((134, 162, 110, 100, 195))

    # Enable content decoding if necessary
    if response.headers.get("Content-Encoding"):
        response.raw.decode_content = True

    with tqdm(unit="B", unit_scale=True, delay=_progress_delay, disable=_disable_progress, desc=desc) as progress:

        # Get the raw data stream from the http response
        stream = StreamingDecoder(response.raw)

        # Decode the response
        if stream.peek(len(array_prefix)) == array_prefix:
            # Response is a fixed length type ndarray
            return decode_ndarray(stream, desc, progress)
        else:
            # Response is something else
            return decode_generic(stream, desc, progress)


def decode_generic(stream, desc, progress):
    """
    Decode a msgpack encoded http response

    This version can handle arbitrary msgpack data types but copies any
    array body several times, so it's slower and more memory hungry. But
    good for small but complicated metadata responses.
    """

    # Download all data as a list of chunks
    data = []
    while this_chunk := stream.read(chunk_size):
        data.append(this_chunk)
        progress.update(len(this_chunk))

    # Concatenate into one big byte array
    data = b''.join(data)

    # Call the msgpack decoder
    return msgpack.unpackb(data, object_hook=decode_hook)


def unpack_equals(unpacker, value):
    obj = unpacker.unpack()
    if obj != value:
        raise RuntimeError("Unexpected value encountered unpacking ndarray")


def decode_ndarray(stream, desc, progress):
    """
    Decode a msgpack encoded ndarray of a fixed size type

    This version handles the easy case where we have a single array of a
    fixed size data type. We decode the array header, allocate a
    numpy.ndarray and receive data directly into the array's buffer.

    This assumes that the "data" map key is encoded last by the server. This
    is not likely to change because we need all of the metadata to arrive
    before the data for efficient decoding.
    """

    # Read the header: we expect a msgpack map here
    max_header_size = 1024
    unpacker = msgpack.Unpacker()
    unpacker.feed(stream.peek(max_header_size))
    n = unpacker.read_map_header()

    # We expect the final map key to be "data". First read all
    # of the other keys
    map_keys = {}
    for _ in range(n-1):
        map_key = unpacker.unpack()
        map_val = unpacker.unpack()
        map_keys[map_key] = map_val

    # ndarrays are identified by {nd : True}
    if "nd" not in map_keys or map_keys["nd"] != True:
        raise RuntimeError("This does not appear to be an encoded ndarray!")

    # Then we should have an entry with key "data" and value equal to an
    # array of msgpack_bin objects. We don't want to read those yet.
    unpack_equals(unpacker, "data")
    nr_bins = unpacker.read_array_header()

    # Get ndarray metadata
    shape = map_keys["shape"]
    dtype = map_keys["type"]
    nbytes = map_keys["nbytes"]

    # Allocate a buffer for the full amount of data
    buf = memoryview(np.empty(nbytes, dtype=np.uint8)).cast("B")
    progress.total = nbytes

    # Skip past the bytes we've interpreted
    stream.skip(unpacker.tell())

    # Read the bin objects into the array's buffer
    offset = 0
    chunk = 1024*1024
    for bin_nr in range(nr_bins):
        # Get number of bytes in this binary object
        bytes_left = stream.read_bin_header()
        # Read the bytes into the array's buffer in chunks
        while bytes_left > 0:
            max_to_read = min(bytes_left, chunk)
            n = stream.readinto(buf[offset:offset+max_to_read])
            bytes_left -= n
            offset += n
            progress.update(n)

    # Wrap the buffer in a suitable ndarray
    arr = np.frombuffer(buf, dtype=dtype).reshape(shape)

    # We should now be at the end of the stream
    if len(stream.read(1)) != 0:
        raise RuntimeError("Unexpected extra data at end of stream!")

    return arr

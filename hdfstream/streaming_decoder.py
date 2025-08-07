#!/bin/env python

import numpy as np

# Big endian int types used to interpret msgpack data
be_uint8  = np.dtype(">u1")
be_uint16 = np.dtype(">u2")
be_uint32 = np.dtype(">u4")


class StreamingDecoder:
    """
    Class for decoding msgpack encoded ndarrays from a stream
    """
    def __init__(self, stream):
        """
        Initialize the stream reader
        """
        self._stream = stream
        self.buf = bytearray() # initially zero length

    def peek(self, n):
        """
        Try to preview the next n bytes from the stream

        This does NOT advance the next byte to be read by readinto().
        Might return fewer than n bytes if we're near the end of the stream.
        Returns zero bytes if we are at the end.
        """

        # Ensure we have n bytes buffered (if we don't hit end of stream)
        while len(self.buf) < n:
            chunk = self._stream.read(n - len(self.buf))
            if not chunk:
                break
            self.buf.extend(chunk)

        # Return a view of up to n bytes from the buffer
        return memoryview(self.buf)[:n]

    def skip(self, n):
        """
        Advance past the next n bytes to be read by read() and readinto()

        This only works if at least n bytes have been peek()'d.
        """
        if n > len(self.buf):
            raise RuntimeError("Attempting to skip more bytes than were peek()'d")

        # Discard n bytes from the start of the buffer
        self.buf = self.buf[n:]

    def readinto(self, b):
        """
        Copy bytes from the stream to the output buffer

        Any previewed bytes are written first, after which we can use the
        readinto() method of the stream to avoid copying subsequent bytes.

        Returns the number of bytes written, which might be less than
        len(outbuf) if we reach the end of the stream.
        """
        mv = memoryview(b)

        # Copy as much as we can/need from the buffer
        nr_from_buf = min(len(self.buf), len(mv))
        mv[:nr_from_buf] = self.buf[:nr_from_buf]

        # Delete copied bytes from the buffer
        self.buf = self.buf[nr_from_buf:]

        # If we still need more bytes, read directly into the output buffer
        if nr_from_buf < len(mv):
            nr_read_into = self._stream.readinto(mv[nr_from_buf:])
            return nr_from_buf + (nr_read_into or 0) # nr_read_into=None at end of stream
        return nr_from_buf

    def read(self, size=-1):
        """Read `size` bytes, consuming buffered data first."""
        if size == -1:
            # Read all: return buffer + rest of stream
            data = bytes(self.buf)
            self.buf = bytearray()
            return data + self._stream.read()
        else:
            # Read from buffer first
            from_buffer = self.buf[:size]
            self.buf = self.buf[size:]
            remaining = size - len(from_buffer)
            if remaining > 0:
                from_stream = self._stream.read(remaining)
                return bytes(from_buffer) + from_stream
            else:
                return bytes(from_buffer)

    def read_bin_header(self):
        """
        Assuming the next bytes are a msgpack bin object, read the header,
        advance to the start of the payload, and return its size in bytes.
        """
        # Ensure we have enough bytes buffered ahead. A msgpack_bin header
        # is 2, 3 or 5 bytes long.
        self.peek(5)

        # Determine the size of the bin object
        if self.buf[0] == 0xc4:
            # One byte length
            nr_bytes = int(np.void(self.buf[1:2]).view(be_uint8))
            self.skip(2)
        elif self.buf[0] == 0xc5:
            # Two byte length
            nr_bytes = int(np.void(self.buf[1:3]).view(be_uint16))
            self.skip(3)
        elif self.buf[0] == 0xc6:
            # Four byte length
            nr_bytes = int(np.void(self.buf[1:5]).view(be_uint32))
            self.skip(5)
        else:
            raise RuntimeError("Next msgpack object is not a msgpack_bin!")
        return nr_bytes

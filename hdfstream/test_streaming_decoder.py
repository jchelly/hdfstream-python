#!/bin/env python

import io
import pytest

from hdfstream.streaming_decoder import StreamingDecoder


test_cases = [(0, 256),
              (1, 256),
              (4, 256),
              (500, 256),
              (500, 193),
              (10000, 113)]


def make_test_stream(nr_bytes, mod_val):
    """
    Create a byte stream with predictable values

    The i'th byte has value (i % mod_val).
    """
    # Create an array of bytes
    data = bytearray(nr_bytes)
    for i in range(nr_bytes):
        data[i] = (i % mod_val)

    # Wrap in a stream
    return StreamingDecoder(io.BytesIO(data))


def verify_output(nr_bytes, mod_val, data):
    assert nr_bytes == len(data)
    for i in range(len(data)):
        assert data[i] == (i % mod_val)


def do_read_all(nr_bytes, mod_val):
    """
    Test reading the stream in a single read call
    """
    stream = make_test_stream(nr_bytes, mod_val)
    data = stream.read()
    verify_output(nr_bytes, mod_val, data)


def test_read_all():
    """
    Try reading a few different stream sizes with read
    """
    for (nr_bytes, mod_val) in test_cases:
        do_read_all(nr_bytes, mod_val)


def do_readinto_all(nr_bytes, mod_val):
    """
    Test reading the stream in a single readinto call
    """
    stream = make_test_stream(nr_bytes, mod_val)
    data = bytearray(nr_bytes)
    stream.readinto(data)
    verify_output(nr_bytes, mod_val, data)


def test_readinto_all():
    """
    Try reading a few different stream sizes with readinto
    """
    for (nr_bytes, mod_val) in test_cases:
        do_readinto_all(nr_bytes, mod_val)


def do_peek_all(nr_bytes, mod_val):
    """
    Try the case where we peek at the full stream first
    """
    stream = make_test_stream(nr_bytes, mod_val)
    data_peek = stream.peek(nr_bytes)
    data_read = stream.read()
    assert data_peek == data_read
    verify_output(nr_bytes, mod_val, data_read)


def test_peek_all():
    """
    Test full peek with a few different stream sizes
    """
    for (nr_bytes, mod_val) in test_cases:
        do_peek_all(nr_bytes, mod_val)


def do_read_chunks(nr_bytes, mod_val):
    """
    Read the full stream in multiple read() calls
    """
    for chunk_size in (1, 2, 3, 10, 27, 500, 20000):
        stream = make_test_stream(nr_bytes, mod_val)
        data = []
        while chunk := stream.read(chunk_size):
            data.append(chunk)
        data = b''.join(data)
        verify_output(nr_bytes, mod_val, data)


def test_read_chunks():
    """
    Try reading a few different streams in chunks
    """
    for (nr_bytes, mod_val) in test_cases:
        do_read_chunks(nr_bytes, mod_val)


def do_readinto_chunks(nr_bytes, mod_val):
    """
    Read the full stream in multiple readinto() calls
    """
    for chunk_size in (1, 2, 3, 10, 27, 500, 20000):
        stream = make_test_stream(nr_bytes, mod_val)
        data = memoryview(bytearray(nr_bytes))
        offset = 0
        while offset < nr_bytes:
            n = stream.readinto(data[offset:offset+chunk_size])
            offset += n
        verify_output(nr_bytes, mod_val, data)


def test_readinto_chunks():
    """
    Try reading a few different streams in chunks
    """
    for (nr_bytes, mod_val) in test_cases:
        do_readinto_chunks(nr_bytes, mod_val)


def do_read_chunks_with_peek(nr_bytes, mod_val, peek_size):
    """
    Read the full stream in multiple read() calls, peeking in between
    """
    for chunk_size in (1, 2, 3, 10, 27, 500, 20000):
        stream = make_test_stream(nr_bytes, mod_val)
        data = []
        offset = 0
        while chunk := stream.read(chunk_size):
            # Read from the stream
            data.append(chunk)
            offset += len(chunk)
            # Peek and verify some bytes
            data_peek = stream.peek(peek_size)
            for i in range(len(data_peek)):
                assert data_peek[i] == (offset+i) % mod_val
        data = b''.join(data)
        verify_output(nr_bytes, mod_val, data)


def test_read_chunks_with_peek():
    """
    Try reading a few different streams in chunks, peeking between reads
    """
    for peek_size in (0, 1, 3, 10, 50, 300):
        for (nr_bytes, mod_val) in test_cases:
            do_read_chunks_with_peek(nr_bytes, mod_val, peek_size)


def do_readinto_chunks_with_peek(nr_bytes, mod_val, peek_size):
    """
    Read the full stream in multiple read() calls, peeking in between
    """
    for chunk_size in (1, 2, 3, 10, 27, 500, 20000):
        stream = make_test_stream(nr_bytes, mod_val)
        data = memoryview(bytearray(nr_bytes))
        offset = 0
        while offset < nr_bytes:
            # Read the next chunk into the buffer
            n = stream.readinto(data[offset:offset+chunk_size])
            offset += n
            # Peek and verify some bytes
            data_peek = stream.peek(peek_size)
            for i in range(len(data_peek)):
                assert data_peek[i] == (offset+i) % mod_val
        verify_output(nr_bytes, mod_val, data)


def test_readinto_chunks_with_peek():
    """
    Try reading a few different streams in chunks, peeking between readintos
    """
    for peek_size in (0, 1, 3, 10, 50, 300):
        for (nr_bytes, mod_val) in test_cases:
            do_readinto_chunks_with_peek(nr_bytes, mod_val, peek_size)


def do_readinto_chunks_with_peek_and_skip(nr_bytes, mod_val, peek_size):
    """
    Read the full stream in multiple read() calls, skipping peeked bytes
    """
    for chunk_size in (1, 2, 3, 10, 27, 500, 20000):
        stream = make_test_stream(nr_bytes, mod_val)
        data = memoryview(bytearray(nr_bytes))
        offset = 0
        while offset < nr_bytes:
            # Read the next chunk into the buffer
            n = stream.readinto(data[offset:offset+chunk_size])
            offset += n
            # Peek and verify some bytes
            data_peek = stream.peek(peek_size)
            for i in range(len(data_peek)):
                assert data_peek[i] == (offset+i) % mod_val
            # Copy the peeked bytes to the output
            data[offset:offset+len(data_peek)] = data_peek
            offset += len(data_peek)
            # Advance the stream past these bytes
            stream.skip(len(data_peek))
        verify_output(nr_bytes, mod_val, data)


def test_readinto_chunks_with_peek_and_skip():
    """
    Try reading a few different streams in chunks, peeking between readintos
    and skipping the peeked bytes
    """
    for peek_size in (0, 1, 3, 10, 50, 300):
        for (nr_bytes, mod_val) in test_cases:
            do_readinto_chunks_with_peek_and_skip(nr_bytes, mod_val, peek_size)

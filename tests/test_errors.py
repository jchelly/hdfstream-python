#!/bin/env python

import pytest
import hdfstream

@pytest.mark.vcr
def test_msgpack_error(eagle_snap_file):
    # Try a request that should generate a msgpack error response
    with pytest.raises(hdfstream.HDFStreamRequestError):
        eagle_snap_file().connection.request_path("does-not-exist")

@pytest.mark.vcr
def test_html_error(server_url):
    # Try a request that should generate a html error response
    with pytest.raises(hdfstream.HDFStreamRequestError):
        root_dir = hdfstream.open(server_url, "/", user="no-such-user", password="no-such-password")

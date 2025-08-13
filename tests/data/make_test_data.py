#!/bin/env python
#
# This script makes some requests to the server and stores the responses
# for later use in unit tests.
#

import hdfstream
import responses
import pickle
import gzip

# Location of the server to use to generate test data
server_url = "https://dataweb.cosma.dur.ac.uk:8443/hdfstream"
connection = hdfstream.connection.Connection.new(server_url, user=None)

def get_msgpack(path, params=None):
    """Make a request and return the response object"""
    path = path.lstrip("/")
    url = f"{server_url}/msgpack/{path}"
    return connection.session.get(url, params=params)

def get_and_store(output_filename, path, params=None):
    response = get_msgpack(path, params)
    data = {
        "method"  : "GET",
        "url"     : response.url,
        "headers" : response.headers,
        "body"    : response.content,
        "status"  : response.status_code,
        }
    with gzip.open(output_filename, "wb") as f:
        pickle.dump(data, f)

# Store some directory listings
get_and_store("responses/root_listing.dat.gz", "/")
get_and_store("responses/EAGLE_dir_listing.dat.gz", "/EAGLE")
get_and_store("responses/EAGLE_FM_dir_listing.dat.gz", "/EAGLE/Fiducial_models")
get_and_store("responses/EAGLE_snap_listing.dat.gz", "/EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000")

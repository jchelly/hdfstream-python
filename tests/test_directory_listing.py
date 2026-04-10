#!/bin/env python

import pytest
from hdfstream import RemoteDirectory

@pytest.mark.vcr
def test_root_listing(server_url):

    import hdfstream
    root = hdfstream.open(server_url, "/")
    assert isinstance(root, RemoteDirectory)

@pytest.mark.vcr
def test_eagle_dir_listing_with_subdirs(server_url):

    import hdfstream
    eagle_dir = hdfstream.open(server_url, "/EAGLE")
    fm_dir = eagle_dir["Fiducial_models"]
    assert len(fm_dir) == 7
    expected_dirs = set(["RefL0012N0188", "RefL0025N0376", "RefL0025N0752", "RecalL0025N0752",
                         "RefL0050N0752", "AGNdT9L0050N0752", "RefL0100N1504"])
    assert set(fm_dir.directories.keys()) == expected_dirs
    assert len(fm_dir.files) == 0

@pytest.mark.vcr
def test_eagle_subdir(server_url):

    import hdfstream
    eagle_dir = hdfstream.open(server_url, "/EAGLE")
    fm_dir = eagle_dir["Fiducial_models"]
    sim_dir = fm_dir["RefL0012N0188"]
    assert sim_dir is eagle_dir["Fiducial_models/RefL0012N0188"]

@pytest.mark.vcr
def test_eagle_subdir_loaded(server_url):

    import hdfstream
    eagle_dir = hdfstream.open(server_url, "/EAGLE")
    fm_dir = eagle_dir["Fiducial_models"]
    fm_dir_list = list(fm_dir) # forces request of the directory listing
    sim_dir = fm_dir["RefL0012N0188"]
    assert sim_dir is eagle_dir["Fiducial_models/RefL0012N0188"]

@pytest.mark.vcr
def test_eagle_dir_listing_with_files(server_url):

    import hdfstream
    eagle_dir = hdfstream.open(server_url, "/EAGLE")
    snap_dir = eagle_dir["Fiducial_models/RefL0012N0188/snapshot_000_z020p000"]
    assert len(snap_dir) == 16
    expected_files = set([f"snap_000_z020p000.{i}.hdf5" for i in range(16)])
    assert set(snap_dir.files.keys()) == expected_files
    for name in snap_dir.files:
        assert isinstance(snap_dir[name], hdfstream.RemoteFile)
    assert len(snap_dir.directories) == 0

@pytest.mark.vcr
def test_non_existent_directory(server_url):

    import hdfstream
    eagle_dir = hdfstream.open(server_url, "/EAGLE")
    with pytest.raises(KeyError):
        sub_dir = eagle_dir["invalid"]

@pytest.mark.vcr
def test_non_existent_directory_already_loaded(server_url):

    import hdfstream
    root_dir = hdfstream.open(server_url, "/")
    eagle_dir = root_dir["EAGLE"]
    subdirs = list(eagle_dir.directories) # ensure listing has been loaded
    with pytest.raises(KeyError):
        sub_dir = eagle_dir["invalid"]

@pytest.mark.vcr
def test_non_existent_subdir_in_directory_already_loaded(server_url):

    import hdfstream
    root_dir = hdfstream.open(server_url, "/")
    eagle_dir = root_dir["EAGLE"]
    subdirs = list(eagle_dir.directories) # ensure listing has been loaded
    with pytest.raises(KeyError):
        # should already know that invalid1 is not a subdir of /EAGLE
        sub_dir = eagle_dir["invalid1/invalid2"]

@pytest.mark.vcr
def test_non_existent_subdir_in_directory_not_already_loaded(server_url):

    import hdfstream
    root_dir = hdfstream.open(server_url, "/")
    eagle_dir = root_dir["EAGLE"]
    with pytest.raises(KeyError):
        # we need to make a request to discover that this doesn't exist
        sub_dir = eagle_dir["invalid1/invalid2"]

@pytest.mark.vcr
def test_eagle_file_listing(server_url):

    import hdfstream
    snap_dir = hdfstream.open(server_url,
                              "/EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000")
    expected_files = set([f"snap_028_z000p000.{i}.hdf5" for i in range(16)])
    assert set(snap_dir.keys()) == expected_files
    assert set(snap_dir.files.keys()) == expected_files
    for filename in expected_files:
        f = snap_dir[filename]
        assert isinstance(f, hdfstream.RemoteFile)
        assert f.is_hdf5()

@pytest.mark.vcr
def test_request_dir_with_file_already_loaded(server_url):

    import hdfstream
    eagle_dir = hdfstream.open(server_url, "/EAGLE")
    snap_file = eagle_dir["Fiducial_models/RefL0012N0188/snapshot_000_z020p000/snap_000_z020p000.0.hdf5"]
    snap_dir  = eagle_dir["Fiducial_models/RefL0012N0188/snapshot_000_z020p000"]
    snap_dir_list = list(snap_dir) # forces request and unpacking of directory listing
    assert snap_dir["snap_000_z020p000.0.hdf5"] is snap_file

@pytest.mark.vcr
def test_request_dir_with_dir_already_loaded(server_url):

    import hdfstream
    eagle_dir = hdfstream.open(server_url, "/EAGLE")
    snap_dir  = eagle_dir["Fiducial_models/RefL0012N0188/snapshot_000_z020p000"]
    sim_dir   = eagle_dir["Fiducial_models/RefL0012N0188"]
    sim_dir_list = list(sim_dir) # forces request and unpacking of directory listing
    assert sim_dir["snapshot_000_z020p000"] is snap_dir

@pytest.mark.vcr
def test_implicit_directory(server_url):
    """
    Test the case where we infer the existence of a directory
    and delay loading the full listing.
    """
    # Open a directory
    import hdfstream
    root_dir = hdfstream.open(server_url, "/")
    snap_dir = root_dir["EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000"]

    # Directories on the path should not have been requested from the server yet
    for dirname in ("EAGLE","EAGLE/Fiducial_models","EAGLE/Fiducial_models/RefL0012N0188"):
        assert root_dir[dirname].unpacked == False

    # Listing an intermediate directory should trigger a request for the full listing
    for dirname in ("EAGLE","EAGLE/Fiducial_models"):
        listing = list(root_dir[dirname])
        assert root_dir["EAGLE"].unpacked

    # Check lazy loading didn't prevent us opening the file or directories
    for dirname in ("EAGLE","EAGLE/Fiducial_models","EAGLE/Fiducial_models/RefL0012N0188",
                    "EAGLE/Fiducial_models/RefL0012N0188/snapshot_028_z000p000"):
        subdir = root_dir[dirname]

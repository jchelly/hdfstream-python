#!/bin/env python

import pytest
import keyring.errors
import hdfstream
from hdfstream.testing import KeyringNotAvailableError

def test_keyring_set_is_disabled():
    with pytest.raises(KeyringNotAvailableError):
        keyring.set_password("_system", "_username", "_password")

def test_keyring_get_is_disabled():
    with pytest.raises(KeyringNotAvailableError):
        password = keyring.get_password("_system", "_username")

def test_alias_not_found():
    config = hdfstream.get_config()
    url, user, use_keyring = config.resolve_alias("no_such_alias", None)
    assert url == "no_such_alias"
    assert user is None
    assert use_keyring == False

def test_alias_not_found_with_user():
    config = hdfstream.get_config()
    url, user, use_keyring = config.resolve_alias("no_such_alias", "username")
    assert url == "no_such_alias"
    assert user == "username"
    assert use_keyring == False

def test_alias():
    config = hdfstream.get_config()
    url, user, use_keyring = config.resolve_alias("example", None)
    assert url == "https://example.com/hdfstream"
    assert user is None
    assert use_keyring == False

def test_alias_with_user():
    config = hdfstream.get_config()
    url, user, use_keyring = config.resolve_alias("example", "username")
    assert url == "https://example.com/hdfstream"
    assert user == "username"
    assert use_keyring == False

def test_alias_yaml_round_trip(tmp_path):

    # Make the test config
    config = hdfstream.Config()
    config.add_alias("test_alias", "test_url", user="test_user", use_keyring=True)

    # Write the config to a file
    filename = tmp_path / "test.yml"
    config.write(filename)

    # Read it back
    config = hdfstream.Config()
    config.read(filename)

    # Check it works
    url, user, use_keyring = config.resolve_alias("test_alias", None)
    assert url == "test_url"
    assert user == "test_user"
    assert use_keyring == True

def test_set_config():

    # Make the test config
    config = hdfstream.Config()
    config.add_alias("test_set_alias", "test_set_url", user="test_set_user", use_keyring=True)
    hdfstream.set_config(config)

    # Check it works
    url, user, use_keyring = config.resolve_alias("test_set_alias", None)
    assert url == "test_set_url"
    assert user == "test_set_user"
    assert use_keyring == True

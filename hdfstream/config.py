#!/bin/env python

import yaml
import platformdirs

#
# Contents of the default configuration file
#
default_config = {
    "aliases" : {
        "cosma" : {
            "url" : "https://dataweb.cosma.dur.ac.uk:8443/hdfstream",
            "user" : None, # username in case authentication is required
            "use_keyring" : False, # fetch password from system keyring if True
            },
    },
}

class Config:
    """
    Class to store module configuration info
    """
    def __init__(self):
        """
        Create a new, empty configuration object
        """
        self._config_path = platformdirs.user_config_path(appname="hdfstream", ensure_exists=True)
        self._config_path = self._config_path / "config.yml"
        self._alias = {}

    def add_alias(self, name, url, user=None, use_keyring=False):
        """
        Add a new alias for the specified URL
        """
        self._alias[name] = {
            "url" : url,
            "user" : user,
            "use_keyring" : use_keyring,
        }

    def write(self, filename=None, mode="x"):
        """
        Write this config object to a yaml file
        """
        if filename is None:
            filename = self._config_path
        config = {"aliases" : self._alias}
        with open(filename, mode) as config_file:
            yaml.dump(config, config_file)

    def read(self, filename=None):
        """
        Read and validate the specified config file
        """
        if filename is None:
            filename = self._config_path
        with open(filename, "r") as config_file:
            config = yaml.safe_load(config_file)

        # Should be a dict with an "aliases" key
        if not isinstance(config, dict) or "aliases" not in config.keys():
            raise TypeError("Config should contain a dict of aliases")

        # Validate aliases in the config file
        for key, val in config["aliases"].items():
            if not isinstance(key, str):
                raise TypeError("Alias names must be strings")
            url = val["url"]
            if not isinstance(url, str):
                raise TypeError("Alias URLs must be strings")
            user = val.get("user", None)
            if user is not None and not isinstance(user, str):
                raise TypeError("Alias user names must be strings")
            use_keyring = val.get("use_keyring", False)
            if not isinstance(use_keyring, bool):
                raise TypeError("Alias use_keyring flag must be bool")
            self._alias[key] = {
                "url" : url,
                "user" : user,
                "use_keyring" : use_keyring,
            }

    def resolve_alias(self, name, user):
        """
        Given an alias, return the corresponding server URL and
        the user name to use. If no match is found, assume the name is
        already a URL and return it.

        If a username is specified, it overrides the stored username.

        Also returns use_keyring, which specifies if we should try to
        access the system keyring.
        """

        use_keyring = False
        alias = self._alias.get(name, None)
        if alias is not None:
            # The specified server name is an alias
            name = alias["url"]
            # Get the username, if it wasn't specified
            if user is None:
                user = alias.get("user", None)
            # Check if we're using the keyring
            use_keyring = alias.get("use_keyring", False)

        return name, user, use_keyring


def _default_config():
    """
    Return a default configuration object
    """
    config = Config()
    config.add_alias("cosma", "https://dataweb.cosma.dur.ac.uk:8443/hdfstream")
    return config


def _read_user_config():
    """
    Try to read the user's default config file
    """
    config = Config()
    config.read()
    return config


_config = None
def get_config():
    """
    Return a Config object

    Reads the user's config file if possible. Writes a new default config
    otherwise.
    """
    global _config
    try:
        _config = _read_user_config()
    except OSError:
        _config = _default_config()
        _config.write()
    return _config

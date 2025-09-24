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

        config_path = platformdirs.user_config_path(appname="hdfstream", ensure_exists=True)
        config_path = config_path / "config.yml"

        # Write the default config file if necessary
        try:
            with open(config_path, "x") as config_file:
                yaml.dump(default_config, config_file)
        except FileExistsError:
            pass

        # Read the current config
        with open(config_path, "r") as config_file:
            self._config = yaml.safe_load(config_file)

        # Set up dict of aliases
        self._alias = {}
        for name in self._config["aliases"].keys():
            self._alias[name] = self._config["aliases"][name]

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

# Read (or create) the config file with server aliases
config = Config()

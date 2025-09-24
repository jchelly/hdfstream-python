#!/bin/env python

import yaml
import platformdirs
import keyring

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
            self._alias[name] = str(self._config["aliases"][name]["url"])

    def resolve_alias(self, name, user, password):
        """
        Given an alias, return the corresponding server URL. If no match is
        found, assume the name is already a URL and return it.

        Also looks up any username and password we should use. If a username
        is set and use_keyring is True, we will use a password from the keyring
        or prompt for the password and store it.

        If a username and password are provided we return those in preference
        to the values from the config file and keyring.
        """

        alias = self._alias.get(name, None)
        if alias is not None:
            # The specified server name is an alias
            name = alias["url"]
            # Get the username, if it wasn't specified
            if user is None:
                user = alias.get("user", None)
            # Get the password, if it wasn't specified and we're using the keyring
            use_keyring = alias.get("use_keyring", False)
            if use_keyring and user is not None and password is None:
                password = keyring.get_password(name, user)
                if password is None:
                    password = getpass.getpass(f"Enter password for {user} at {name} (will store in system keyring): ")
                    # TODO: only store passwords that work!
                    keyring.set_password(name, user, password)
        return name, user, password

# Read (or create) the config file with server aliases
config = Config()

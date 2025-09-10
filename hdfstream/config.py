#!/bin/env python

import yaml
import platformdirs

#
# Contents of the default configuration file
#
default_config = {
    "aliases" : {
        "cosma" : {"url" : "https://dataweb.cosma.dur.ac.uk:8443/hdfstream",}
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

    def get_url(self, name):
        """
        Given an alias, return the corresponding server URL. If no match is
        found, assume the name is already a URL and return it.
        """
        if name in self._alias:
            return self._alias[name]
        else:
            return name

# Read (or create) the config file with server aliases
config = Config()

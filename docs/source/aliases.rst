Server aliases
==============

In order to avoid the need to enter a long server URL every time a
connection is opened, the module provides a yaml configuration file
which can be used to define an `alias`, or short name, for the
server. On linux this file is stored in::

    ~/.config/hdfstream/config.yml

The default configuration looks like this::

    aliases:
      cosma:
        url: https://dataweb.cosma.dur.ac.uk:8443/hdfstream
        use_keyring: false
        user: null

This defines an alias called ``cosma`` for the URL
``https://dataweb.cosma.dur.ac.uk:8443/hdfstream``.

Authentication
--------------

The server might require authentication for access to certain
datasets. The ``user`` field in the config file can be used to specify
a default username to use when making requests to the corresponding
server.

If the ``use_keyring`` field is ``true`` and a username is set, then
the module will try to use the system keyring (via the `python keyring
module <https://pypi.org/project/keyring/>`__) to fetch the
password. If the password is not in the keyring then the module
prompts for a password and stores it in the keyring if it works.

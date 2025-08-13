Connecting to the service
-------------------------

The data files available on the server are arranged in a virtual directory
structure. To access files we connect to the server and request a listing of
the directory which contains the files we're interested in. This is done
using the :py:func:`hdfstream.open` function::

  import hdfstream
  root = hdfstream.open("https://localhost:8443/hdfstream", "/")

Here, the first parameter is the server URL and the second is the
virtual directory on the server which we'd like to access. This
command returns a :py:class:`hdfstream.RemoteDirectory` object.

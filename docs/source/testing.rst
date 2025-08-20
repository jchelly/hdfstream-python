Testing
-------

Unit test implementation
^^^^^^^^^^^^^^^^^^^^^^^^

Since this module accesses a web service, writing self contained unit
tests which can be run without network access is not totally
straightforward.

Unit tests for this module are implemented using vcrpy
(https://vcrpy.readthedocs.io/en/latest/) and pytest-recording
(https://github.com/kiwicom/pytest-recording). This works as follows:

  * Tests are written to access the server as normal
  * The tests are run in a mode where vcrpy records all http requests
    and responses to a "cassette" file
  * On subsequent test runs vcrpy can generate mock http responses
    using the stored data

The pytest-recording plugin provides a mechanism to configure vcrpy in
pytest unit tests using decorators.

Writing unit tests
^^^^^^^^^^^^^^^^^^

Http responses are stored as gzipped messagepack for compactness. The
module :py:mod:`hdfstream.testing` provides the vcrpy serializer and
persister classes used to implement this.

To configure pytest to record http responses in messagepack format,
this line should be included in ``conftest.py``::

  from hdfstream.testing import pytest_recording_configure, vcr_config

Then the decorator ``@pytest.mark.vcr`` can be added to unit test
functions to enable recording of http responses. E.g.::

  @pytest.mark.vcr
  def test_dir_listing():
    import hdfstream
    root = hdfstream.open("https://localhost:8443/hdfstream", "/")
    ...

To run the unit tests in a "live" mode where real http requests are
made and the responses are recorded:

  pytest --record-mode=once

This will create a ``cassettes`` directory with the encoded
responses. After that the unit tests can be run in offline mode with
just::

  pytest

In this case the stored responses will be used and no network access
is required. This can be used to write tests for other modules which
make use of the :py:mod:`hdfstream` module.

"""Pytest configuration for the tests/ directory.

The integration test scripts in this directory (test_auth.py, test_connect.py,
etc.) are standalone scripts that execute side-effects at import time.
This conftest excludes them from pytest collection so that ``pytest``
discovers only the unit-test files.
"""

collect_ignore = [
    "test_auth.py",
    "test_connect.py",
    "test_subscribe.py",
    "test_publish.py",
    "test_amqp.py",
]

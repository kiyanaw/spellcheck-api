"""Fixtures for integration tests."""

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def api_url(request):
    import os
    url = os.environ.get("SPELLCHECK_API_URL")
    if not url:
        pytest.skip("SPELLCHECK_API_URL not set")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def api_key(request):
    import os
    key = os.environ.get("SPELLCHECK_API_KEY")
    if not key:
        pytest.skip("SPELLCHECK_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def api_headers(api_key):
    return {"x-api-key": api_key, "Content-Type": "application/json"}

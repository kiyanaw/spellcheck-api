"""Smoke tests — reachability and auth."""

import requests


def test_api_is_reachable(api_url, api_headers):
    resp = requests.post(
        f"{api_url}/bulk-lookup",
        json={"languageCode": "crk", "words": ["êkwa"]},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 200


def test_api_requires_auth(api_url):
    resp = requests.post(
        f"{api_url}/bulk-lookup",
        json={"languageCode": "crk", "words": ["êkwa"]},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    assert resp.status_code == 403

"""Integration tests for POST /spellcheck/bulk-lookup."""

import pytest
import requests

LANGUAGES = [
    ("crk", "êkwa"),
    ("crgn", "êkwa"),
    ("otwc", "niin"),
    ("otwr", "niin"),
    ("ciw", "niin"),
]


@pytest.mark.parametrize("language_code,word", LANGUAGES)
def test_bulk_lookup_returns_200(api_url, api_headers, language_code, word):
    resp = requests.post(
        f"{api_url}/spellcheck/bulk-lookup",
        json={"language_code": language_code, "words": [word]},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)


@pytest.mark.parametrize("language_code,word", LANGUAGES)
def test_bulk_lookup_response_structure(api_url, api_headers, language_code, word):
    resp = requests.post(
        f"{api_url}/spellcheck/bulk-lookup",
        json={"language_code": language_code, "words": [word]},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert word in body
    assert isinstance(body[word], list)


def test_bulk_lookup_known_word_has_analyses(api_url, api_headers):
    resp = requests.post(
        f"{api_url}/spellcheck/bulk-lookup",
        json={"language_code": "crk", "words": ["êkwa"]},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "êkwa" in body
    assert len(body["êkwa"]) > 0


def test_bulk_lookup_unknown_word_has_suggestions(api_url, api_headers):
    resp = requests.post(
        f"{api_url}/spellcheck/bulk-lookup",
        json={"language_code": "crk", "words": ["ekwaa"]},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "_suggestions" in body


def test_bulk_lookup_invalid_body_returns_400(api_url, api_headers):
    resp = requests.post(
        f"{api_url}/spellcheck/bulk-lookup",
        data="not json",
        headers={**api_headers, "Content-Type": "application/json"},
        timeout=30,
    )
    assert resp.status_code == 400


def test_bulk_lookup_missing_fields_returns_400(api_url, api_headers):
    resp = requests.post(
        f"{api_url}/spellcheck/bulk-lookup",
        json={"language_code": "crk"},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 400

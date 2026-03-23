"""Integration tests for POST /suggest."""

import pytest
import requests

LANGUAGES = [
    ("bla", "oki"),
    ("ciw", "niin"),
    ("crgn", "êkwa"),
    ("crk", "êkwa"),
    ("cwd", "êkwa"),
    ("gle", "agus"),
    ("otwc", "niin"),
    ("otwr", "niin"),
]


@pytest.mark.parametrize("language_code,word", LANGUAGES)
def test_suggest_returns_200(api_url, api_headers, language_code, word):
    resp = requests.post(
        f"{api_url}/suggest",
        json={"languageCode": language_code, "words": [word]},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)


@pytest.mark.parametrize("language_code,word", LANGUAGES)
def test_suggest_response_values_are_lists(api_url, api_headers, language_code, word):
    resp = requests.post(
        f"{api_url}/suggest",
        json={"languageCode": language_code, "words": [word]},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 200
    body = resp.json()
    for value in body.values():
        assert isinstance(value, list)
        assert all(isinstance(item, str) for item in value)


def test_suggest_invalid_body_returns_400(api_url, api_headers):
    resp = requests.post(
        f"{api_url}/suggest",
        data="not json",
        headers={**api_headers, "Content-Type": "application/json"},
        timeout=30,
    )
    assert resp.status_code == 400


def test_suggest_missing_language_code_returns_400(api_url, api_headers):
    resp = requests.post(
        f"{api_url}/suggest",
        json={"words": ["êkwa"]},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 400


def test_suggest_missing_words_returns_400(api_url, api_headers):
    resp = requests.post(
        f"{api_url}/suggest",
        json={"languageCode": "crk"},
        headers=api_headers,
        timeout=30,
    )
    assert resp.status_code == 400

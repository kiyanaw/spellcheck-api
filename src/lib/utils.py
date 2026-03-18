"""
Utility functions for the spellcheck Lambda.
"""

import json

HEADERS = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}


def prioritize_particles(analyses):
    """
    Prioritize particles (Ipc) first in analysis results.

    When a word has multiple analyses (e.g., both Ipc and V/N), particles
    are almost always (99%+) the intended reading. This function sorts
    analyses to place Ipc analyses first.
    """
    return sorted(analyses, key=lambda a: (0 if '+Ipc' in a else 1))


def parse_request_body(body):
    """
    Parse request body and extract language code and words.

    Returns dict with {languageCode, words} or None if invalid.
    """
    if not body:
        return None

    try:
        parsed = json.loads(body)

        # New format: { languageCode: "crk", words: [...] }
        if isinstance(parsed, dict) and parsed.get('languageCode') and parsed.get('words'):
            return {
                'languageCode': parsed['languageCode'],
                'words': parsed['words'],
            }

        # Fallback: assume array of words, default to 'crk'
        if isinstance(parsed, list):
            return {
                'languageCode': 'crk',
                'words': parsed,
            }

        return None
    except (json.JSONDecodeError, TypeError):
        return None


def error_response(status_code, message):
    """Create an error response."""
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps({'message': message}),
    }


def success_response(status_code, data):
    """Create a success response."""
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(data),
    }

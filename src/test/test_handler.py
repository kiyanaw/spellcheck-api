"""Tests for the main Lambda handler (index.py)."""

import json
from unittest.mock import patch


def make_event(path, body):
    return {
        'path': path,
        'body': json.dumps(body),
    }


class TestHandlerRouting:
    def test_unknown_path_returns_404(self):
        import index
        event = {'path': '/unknown'}
        response = index.handler(event)
        assert response['statusCode'] == 404

    def test_missing_path_returns_404(self):
        import index
        response = index.handler({})
        assert response['statusCode'] == 404


class TestBulkLookup:
    def test_invalid_body_returns_400(self):
        import index
        event = {'path': '/spellcheck/bulk-lookup', 'body': 'invalid-json'}
        response = index.handler(event)
        assert response['statusCode'] == 400

    def test_missing_language_code_returns_400(self):
        import index
        event = make_event('/spellcheck/bulk-lookup', {'words': ['word']})
        response = index.handler(event)
        assert response['statusCode'] == 400

    def test_missing_words_returns_400(self):
        import index
        event = make_event('/spellcheck/bulk-lookup', {'languageCode': 'crk'})
        response = index.handler(event)
        assert response['statusCode'] == 400

    def test_words_not_array_returns_400(self):
        import index
        event = make_event('/spellcheck/bulk-lookup', {'languageCode': 'crk', 'words': 'word'})
        response = index.handler(event)
        assert response['statusCode'] == 400

    @patch('index.transducers')
    def test_successful_bulk_lookup(self, mock_transducers):
        import index
        mock_transducers.analyze_strict.return_value = {
            'itwêw': ['itwêw+V+AI+Ind+3Sg'],
            'êkwa': ['êkwa+Ipc'],
        }
        mock_transducers.analyze_relaxed.return_value = {}
        mock_transducers.generate_strict.return_value = {}

        event = make_event('/spellcheck/bulk-lookup', {
            'languageCode': 'crk',
            'words': ['itwêw', 'êkwa'],
        })
        response = index.handler(event)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'itwêw' in body
        assert body['itwêw'] == ['itwêw+V+AI+Ind+3Sg']

    @patch('index.transducers')
    def test_bulk_lookup_with_suggestions(self, mock_transducers):
        import index
        mock_transducers.analyze_strict.return_value = {'notaword': []}
        mock_transducers.analyze_relaxed.return_value = {'notaword': ['notaword+V+AI+Ind+3Sg']}
        mock_transducers.generate_strict.return_value = {'notaword+V+AI+Ind+3Sg': ['correction']}

        event = make_event('/spellcheck/bulk-lookup', {
            'languageCode': 'crk',
            'words': ['notaword'],
        })
        response = index.handler(event)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['notaword'] == []
        assert '_suggestions' in body
        assert body['_suggestions']['notaword'] == ['correction']

    @patch('index.transducers')
    def test_character_normalization_applied(self, mock_transducers):
        import index
        mock_transducers.analyze_strict.return_value = {'itwêw': ['itwêw+V+AI+Ind+3Sg']}
        mock_transducers.analyze_relaxed.return_value = {}
        mock_transducers.generate_strict.return_value = {}

        # Send macron version, expect circumflex to be used for lookup
        event = make_event('/spellcheck/bulk-lookup', {
            'languageCode': 'crk',
            'words': ['itwēw'],  # macron ē
        })
        response = index.handler(event)

        assert response['statusCode'] == 200
        # analyze_strict should have been called with circumflex version
        call_args = mock_transducers.analyze_strict.call_args
        assert 'itwêw' in call_args[0][0]

        # Result should be keyed by original word
        body = json.loads(response['body'])
        assert 'itwēw' in body


class TestSuggest:
    def test_invalid_body_returns_400(self):
        import index
        event = {'path': '/spellcheck/suggest', 'body': 'invalid-json'}
        response = index.handler(event)
        assert response['statusCode'] == 400

    @patch('index.transducers')
    def test_successful_suggest(self, mock_transducers):
        import index
        mock_transducers.analyze_relaxed.return_value = {
            'notaword': ['notaword+V+AI+Ind+3Sg'],
        }
        mock_transducers.generate_strict.return_value = {
            'notaword+V+AI+Ind+3Sg': ['correction'],
        }

        event = make_event('/spellcheck/suggest', {
            'languageCode': 'crk',
            'words': ['notaword'],
        })
        response = index.handler(event)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body.get('notaword') == ['correction']

    @patch('index.transducers')
    def test_suggest_no_results(self, mock_transducers):
        import index
        mock_transducers.analyze_relaxed.return_value = {'notaword': []}
        mock_transducers.generate_strict.return_value = {}

        event = make_event('/spellcheck/suggest', {
            'languageCode': 'crk',
            'words': ['notaword'],
        })
        response = index.handler(event)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body == {}

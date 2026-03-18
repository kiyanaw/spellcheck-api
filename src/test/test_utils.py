"""Tests for lib/utils.py"""

import json
from lib.utils import prioritize_particles, parse_request_body, error_response, success_response, HEADERS


class TestPrioritizeParticles:
    def test_ipc_sorted_first(self):
        analyses = ['word+N+Sg', 'word+Ipc', 'word+V+II']
        result = prioritize_particles(analyses)
        assert result[0] == 'word+Ipc'

    def test_no_ipc_order_preserved(self):
        analyses = ['word+N+Sg', 'word+V+II']
        result = prioritize_particles(analyses)
        assert result == ['word+N+Sg', 'word+V+II']

    def test_empty_list(self):
        assert prioritize_particles([]) == []

    def test_all_ipc(self):
        analyses = ['word+Ipc', 'other+Ipc']
        result = prioritize_particles(analyses)
        assert all('+Ipc' in a for a in result)

    def test_multiple_ipc(self):
        analyses = ['a+N', 'b+Ipc', 'c+V', 'd+Ipc']
        result = prioritize_particles(analyses)
        assert result[0] in ('b+Ipc', 'd+Ipc')
        assert result[1] in ('b+Ipc', 'd+Ipc')


class TestParseRequestBody:
    def test_new_format(self):
        body = json.dumps({'languageCode': 'crk', 'words': ['word1', 'word2']})
        result = parse_request_body(body)
        assert result == {'languageCode': 'crk', 'words': ['word1', 'word2']}

    def test_array_fallback(self):
        body = json.dumps(['word1', 'word2'])
        result = parse_request_body(body)
        assert result == {'languageCode': 'crk', 'words': ['word1', 'word2']}

    def test_none_body(self):
        assert parse_request_body(None) is None

    def test_empty_string(self):
        assert parse_request_body('') is None

    def test_invalid_json(self):
        assert parse_request_body('not-json') is None

    def test_invalid_format(self):
        body = json.dumps({'unexpected': 'format'})
        assert parse_request_body(body) is None


class TestResponses:
    def test_error_response(self):
        resp = error_response(400, 'Bad request')
        assert resp['statusCode'] == 400
        assert resp['headers'] == HEADERS
        assert json.loads(resp['body']) == {'message': 'Bad request'}

    def test_success_response(self):
        data = {'word': ['analysis1']}
        resp = success_response(200, data)
        assert resp['statusCode'] == 200
        assert resp['headers'] == HEADERS
        assert json.loads(resp['body']) == data

    def test_cors_headers_present(self):
        resp = success_response(200, {})
        assert resp['headers']['Access-Control-Allow-Origin'] == '*'
        assert resp['headers']['Access-Control-Allow-Methods'] == 'OPTIONS,POST,GET'

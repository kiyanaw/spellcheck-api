"""
Spellcheck Lambda Function (Python / hfst-altlab weighted)

Endpoints:
  POST /bulk-lookup - Analyze multiple words
  POST /suggest     - Get suggestions for unknown words

Request body:
  { "languageCode": "crk", "words": ["word1", "word2", ...] }
"""

from lib import special_processing, transducers
from lib.utils import parse_request_body, error_response, success_response


def _process_words(words, language_code):
    """Apply lowercasing and language-specific character normalization to words."""
    processor = special_processing.get_language_processor(language_code)
    if processor and hasattr(processor, 'process_characters'):
        return [processor.process_characters(w.lower()) for w in words]
    return [w.lower() for w in words]


def _create_word_mapping(original_words, processed_words):
    """Create mapping from processed words back to original words."""
    mapping = {}
    for original, processed in zip(original_words, processed_words):
        if processed != original:
            mapping[processed] = original
    return mapping


def _map_results_to_original(analysis_result, word_mapping):
    """Map analysis results back to original words."""
    result = {}
    for processed_word, analyses in analysis_result.items():
        original_word = word_mapping.get(processed_word, processed_word)
        result[original_word] = analyses
    return result


def _check_unknowns(items, language_code):
    """Check unknown words and generate suggestions."""
    final = {}
    result = transducers.analyze_relaxed(items, language_code)
    print('relaxed result:', result)

    # Map all analyses back to their original words
    original_lookup = {}
    for key, value in result.items():
        if value:
            for analysis in value:
                original_lookup[analysis] = key

    print('original_lookup:', original_lookup)

    # Cap analyses to avoid OOM on languages with large relaxed FSTs (e.g. otwr)
    to_lookup = list(original_lookup.keys())[:100]
    if to_lookup:
        suggested = transducers.generate_strict(to_lookup, language_code)
        print('suggested:', suggested)

        for key, forms in suggested.items():
            if forms:
                original_word = original_lookup[key]
                if original_word not in final:
                    final[original_word] = []
                for suggestion in forms:
                    if suggestion not in final[original_word]:
                        final[original_word].append(suggestion)

    return final


def _bulk_lookup(event):
    parsed = parse_request_body(event.get('body'))

    if not parsed:
        return error_response(400, 'Invalid body format. Expected { languageCode: string, words: string[] } or string[]')

    language_code = parsed.get('languageCode')
    words = parsed.get('words')

    if not language_code or not isinstance(language_code, str):
        return error_response(400, 'languageCode is required and must be a string')

    if not isinstance(words, list):
        return error_response(400, 'words must be an array')

    try:
        processed_words = _process_words(words, language_code)
        print('Processed words:', processed_words)

        word_mapping = _create_word_mapping(words, processed_words)

        analysis_result = transducers.analyze_strict(processed_words, language_code)
        print('analysisResult:', analysis_result)

        result = _map_results_to_original(analysis_result, word_mapping)
        print('result:', result)

        try:
            unknowns = [w for w, analyses in result.items() if not analyses]
            if unknowns:
                result['_suggestions'] = _check_unknowns(unknowns, language_code)
        except Exception as e:
            print('Error generating suggestions:', e)

        print('final:', result)
        return success_response(200, result)
    except Exception as e:
        print('Error in bulk lookup:', e)
        return error_response(500, str(e))


def _suggest(event):
    parsed = parse_request_body(event.get('body'))

    if not parsed:
        return error_response(400, 'Invalid body format. Expected { languageCode: string, words: string[] } or string[]')

    language_code = parsed.get('languageCode')
    words = parsed.get('words')

    if not language_code or not isinstance(language_code, str):
        return error_response(400, 'languageCode is required and must be a string')

    if not isinstance(words, list):
        return error_response(400, 'words must be an array')

    try:
        processed_words = _process_words(words, language_code)
        print('Processed words:', processed_words)

        word_mapping = _create_word_mapping(words, processed_words)

        suggestion_result = _check_unknowns(processed_words, language_code)
        print('suggestionResult:', suggestion_result)

        final = {}
        for processed_word, suggestions in suggestion_result.items():
            original_word = word_mapping.get(processed_word, processed_word)
            final[original_word] = suggestions

        print('final:', final)
        return success_response(200, final)
    except Exception as e:
        print('Error in suggest:', e)
        return error_response(500, str(e))


def handler(event, context=None):
    path = event.get('path')

    if path == '/spellcheck/bulk-lookup':
        return _bulk_lookup(event)
    elif path == '/spellcheck/suggest':
        return _suggest(event)
    else:
        return error_response(404, 'Not found')

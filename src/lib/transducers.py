"""
Transducer management and analysis functions.

Handles loading and using FST transducers for word analysis.
Transducers are loaded from EFS each time (not cached in memory)
to avoid keeping large objects (hundreds of MB) in memory.
The FST files themselves are cached on EFS after first download.
"""

from lib import fst as fst_module
from lib import special_processing
from lib.utils import prioritize_particles


def _extract_analyses(raw_results):
    """
    Extract analysis strings from transducer lookup results.

    hfst_altlab may return FullAnalysis objects (with .analysis/.weight attrs),
    (analysis, weight) tuples, or plain strings.
    Sorts by weight (ascending = more likely) if weights are available.
    """
    if not raw_results:
        return []

    first = raw_results[0]

    # FullAnalysis objects from hfst_altlab (has .tokens and .weight)
    if hasattr(first, 'tokens'):
        sorted_results = sorted(raw_results, key=lambda x: x.weight)
        return [''.join(t for t in item.tokens if not t.startswith('@')) for item in sorted_results]

    # FullAnalysis objects from older hfst_altlab (has .analysis and .weight)
    if hasattr(first, 'analysis'):
        sorted_results = sorted(raw_results, key=lambda x: x.weight)
        return [item.analysis for item in sorted_results]

    # Analysis objects from hfst_altlab (has .lemma, .prefixes, .suffixes)
    if hasattr(first, 'lemma'):
        if hasattr(first, 'weight'):
            raw_results = sorted(raw_results, key=lambda x: x.weight)
        return [''.join(item.prefixes) + item.lemma + ''.join(item.suffixes) for item in raw_results]

    # (analysis, weight) tuples
    if isinstance(first, (tuple, list)):
        sorted_results = sorted(raw_results, key=lambda x: x[1])
        return [item[0] for item in sorted_results]

    return list(raw_results)


def _load_transducer_file(fst_path):
    """Import hfst_altlab lazily and return a TransducerFile instance."""
    from hfst_altlab import TransducerFile  # noqa: PLC0415 — lazy import for testability
    return TransducerFile(fst_path)


def _get_transducer(language_code, fst_type):
    """Load a transducer for the given language and FST type. Returns None if not available."""
    processor = special_processing.get_language_processor(language_code)
    if not processor:
        raise ValueError(f'No language processor found for language: {language_code}')
    if not hasattr(processor, 'FST_FILES'):
        raise ValueError(f'No FST_FILES defined for language: {language_code}')
    if not processor.FST_FILES.get(fst_type):
        return None

    file_name = processor.FST_FILES[fst_type]
    fst_path = fst_module.download_fst_from_s3(file_name)
    return _load_transducer_file(fst_path)


def get_strict_analyzer(language_code):
    """Load strict analyzer for a language from EFS."""
    processor = special_processing.get_language_processor(language_code)
    if not processor:
        raise ValueError(f'No language processor found for language: {language_code}')
    if not hasattr(processor, 'FST_FILES') or not processor.FST_FILES.get('strict-analyzer'):
        raise ValueError(f'No strict-analyzer FST file defined for language: {language_code}')

    file_name = processor.FST_FILES['strict-analyzer']
    fst_path = fst_module.download_fst_from_s3(file_name)
    return _load_transducer_file(fst_path)


def get_relaxed_analyzer(language_code):
    """Load relaxed analyzer for a language from EFS. Returns None if not available."""
    try:
        return _get_transducer(language_code, 'relaxed-analyzer')
    except Exception as e:
        print(f'Failed to load relaxed analyzer for {language_code}: {e}')
        return None


def get_strict_generator(language_code):
    """Load strict generator for a language from EFS. Returns None if not available."""
    try:
        return _get_transducer(language_code, 'strict-generator')
    except Exception as e:
        print(f'Failed to load strict generator for {language_code}: {e}')
        return None


def analyze_strict(lookup, language_code):
    """
    Analyze words using strict analyzer.

    Returns a dict mapping words to arrays of analyses.
    Uses weighted lookup when available, sorting by weight (lower = more likely).
    """
    transducer = get_strict_analyzer(language_code)
    result = {}

    for word in lookup:
        try:
            # Try weighted lookup first for better ranking; fall back if FST is unweighted
            raw = None
            if hasattr(transducer, 'weighted_lookup_full_analysis'):
                raw = transducer.weighted_lookup_full_analysis(word)
            if not raw:
                raw = transducer.lookup(word)

            analyses = _extract_analyses(raw)
            # Filter error analyses
            filtered = [a for a in analyses if '+Err/' not in a and 'Err/Frag' not in a]
            result[word] = prioritize_particles(filtered)
        except Exception as e:
            print(f'Error looking up word "{word}": {e}')
            result[word] = []

    return result


def _is_error_analysis(item):
    """Return True if an analysis result contains error tags."""
    if hasattr(item, 'tokens'):
        joined = ''.join(t for t in item.tokens if not t.startswith('@'))
        return '+Err/' in joined or 'Err/Frag' in joined
    if hasattr(item, 'suffixes'):
        suffixes = ''.join(item.suffixes)
        return '+Err/' in suffixes or 'Err/Frag' in suffixes
    return '+Err/' in str(item) or 'Err/Frag' in str(item)


def analyze_relaxed(lookup, language_code):
    """
    Analyze words using relaxed analyzer.

    Returns a dict mapping words to raw analysis objects (not strings), so they
    can be passed directly to the generator's lookup method. Returns empty arrays
    if no relaxed analyzer is available.
    """
    transducer = get_relaxed_analyzer(language_code)
    result = {}

    if not transducer:
        for word in lookup:
            result[word] = []
        return result

    for word in lookup:
        try:
            raw = None
            if hasattr(transducer, 'weighted_lookup_full_analysis'):
                raw = transducer.weighted_lookup_full_analysis(word)
            if not raw:
                raw = transducer.lookup(word)

            if raw and hasattr(raw[0], 'weight'):
                raw = sorted(raw, key=lambda x: x.weight)

            result[word] = [item for item in (raw or []) if not _is_error_analysis(item)]
        except Exception as e:
            print(f'Error looking up word "{word}": {e}')
            result[word] = []

    return result


def generate_strict(lookup, language_code):
    """
    Generate word forms using strict generator.

    Returns a dict mapping analyses to arrays of generated forms.
    Returns empty arrays if no generator is available.
    """
    transducer = get_strict_generator(language_code)
    result = {}

    if not transducer:
        for word in lookup:
            result[word] = []
        return result

    for word in lookup:
        try:
            raw = transducer.lookup(word)
            result[word] = _extract_analyses(raw)
        except Exception as e:
            print(f'Error generating for "{word}": {e}')
            result[word] = []

    return result

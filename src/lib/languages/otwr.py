"""
Special processing functions for Nishnaabemowin (Odawa - Rhodes) (otwr) language.
"""

import re

FST_FILES = {
    'strict-analyzer': 'morphophonologyclitics_analyze.hfstol',
    'relaxed-analyzer': 'morphophonologyclitics_analyze_relaxed.hfstol',
    'strict-generator': 'morphophonologyclitics_generate.hfstol',
}

_PUNCTUATION = re.compile(r'[.,/#!$%\^&\*;:{}=_`~()]')


def process_characters(text):
    """Strip punctuation for OTWR normalization."""
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text).strip()

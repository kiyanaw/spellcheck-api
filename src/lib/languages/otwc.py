"""
Special processing functions for Nishnaabemwin (Corbiere-style) (otwc) language.
"""

import re

FST_FILES = {
    'strict-analyzer': 'morphophonologyclitics_analyze_mcor_spelling.hfstol',
    'relaxed-analyzer': 'morphophonologyclitics_analyze_mcor_spelling_relaxed.hfstol',
    'strict-generator': 'morphophonologyclitics_generate_mcor_spelling.hfstol',
}

_PUNCTUATION = re.compile(r'[.,/#!$%\^&\*;:{}=_`~()]')


def process_characters(text):
    """Strip punctuation for OTWC normalization."""
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text).strip()

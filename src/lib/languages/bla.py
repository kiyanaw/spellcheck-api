"""
Special processing functions for Siksika (Blackfoot) (bla) language.
"""

import re

FST_FILES = {
    'strict-analyzer': 'bla-analyser-gt-norm.hfstol',
    'relaxed-analyzer': 'bla-analyser-gt-desc.hfstol',
    'strict-generator': 'bla-generator-gt-norm.hfstol',
}

_PUNCTUATION = re.compile(r'[.,/#!$%\^&\*;:{}=_`~()]')


def process_characters(text):
    """Strip punctuation for BLA normalization."""
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text).strip()

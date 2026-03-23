"""
Special processing functions for Gaeilge (Irish) (gle) language.
"""

import re

FST_FILES = {
    'strict-analyzer': 'gle-analyser-gt-norm.hfstol',
    'relaxed-analyzer': 'gle-analyser-gt-desc.hfstol',
    'strict-generator': 'gle-generator-gt-norm.hfstol',
}

_PUNCTUATION = re.compile(r'[.,/#!$%\^&\*;:{}=_`~()]')


def process_characters(text):
    """Strip punctuation for GLE normalization."""
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text).strip()

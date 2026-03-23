"""
Special processing functions for Anishnaabemowin (Ojibwe) (ciw) language.
"""

import re

FST_FILES = {
    'strict-analyzer': 'ojibwe.strict.analyzer.hfstol',
    'relaxed-analyzer': 'ojibwe.relaxed.analyzer.hfstol',
    'strict-generator': 'ojibwe.strict.generator.hfstol',
}

_PUNCTUATION = re.compile(r'[.,/#!$%\^&\*;:{}=_`~()]')


def process_characters(text):
    """Strip punctuation for CIW normalization."""
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text).strip()

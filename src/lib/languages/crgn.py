"""
Special processing functions for Michif (Northern) (crgn) language.

Note: Currently uses the same FST files as CRK since CRGN doesn't have
its own FST files yet.
"""

import re

FST_FILES = {
    'strict-analyzer': 'crk-strict-analyzer-giellaltbuild.hfstol',
    'relaxed-analyzer': 'crk-relaxed-analyzer-giellaltbuild.hfstol',
    'strict-generator': 'crk-strict-generator-giellaltbuild.hfstol',
}

_PUNCTUATION = re.compile(r'[.,/#!$%\^&\*;:{}=_`~()]')


def process_characters(text):
    """
    Convert macron diacritics to circumflex diacritics and strip punctuation.
    """
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text
        .replace('ā', 'â')
        .replace('ī', 'î')
        .replace('ō', 'ô')
        .replace('ē', 'ê')
    ).strip()

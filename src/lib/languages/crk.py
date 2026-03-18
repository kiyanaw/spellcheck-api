"""
Special processing functions for Nêhiyawêwin (Plains Cree Y-dialect) (crk) language.
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
    This is standard normalization for Plains Cree orthography.
    """
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text
        .replace('ā', 'â')
        .replace('ī', 'î')
        .replace('ō', 'ô')
        .replace('ē', 'ê')
    ).strip()

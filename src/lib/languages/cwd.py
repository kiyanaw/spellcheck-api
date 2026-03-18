"""
Special processing functions for Nīhithawīwin (Woods Cree TH-dialect) (cwd) language.
"""

import re

FST_FILES = {
    'strict-analyzer': 'cwd-analyser-gt-norm.hfstol',
    'relaxed-analyzer': 'cwd-analyser-gt-desc.hfstol',
    'strict-generator': 'cwd-generator-gt-norm.hfstol',
}

_PUNCTUATION = re.compile(r'[.,/#!$%\^&\*;:{}=_`~()]')


def process_characters(text):
    """Strip punctuation for CWD normalization."""
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text).strip()

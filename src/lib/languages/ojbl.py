"""
Special processing functions for Border Lakes Ojibwe (ojbl) language.

FSTs come from the ishkodens-fst project, which builds them with foma. Upload the
`full_lexicon_*.foma` builds with an `ojbl-` prefix; the upload script converts them
to `.hfstol`.

foma names its files from the opposite direction to HFST: foma's `*_generate` FST maps
surface forms to analyses, which is what HFST lookup calls an analyzer. So the analyzers
below point at the `generate` builds and the generator at the `analyze` build.

The relaxed analyzer is a rule-based spelling model with no weights, so suggestions are
not ranked.
"""

import re

FST_FILES = {
    'strict-analyzer': 'ojbl-full_lexicon_generate.hfstol',
    'relaxed-analyzer': 'ojbl-full_lexicon_generate_relaxed.hfstol',
    'strict-generator': 'ojbl-full_lexicon_analyze.hfstol',
}

_PUNCTUATION = re.compile(r'[.,/#!$%\^&\*;:{}=_`~()]')


def process_characters(text):
    """Strip punctuation for OJBL normalization."""
    if not text or not isinstance(text, str):
        return text

    return _PUNCTUATION.sub('', text).strip()

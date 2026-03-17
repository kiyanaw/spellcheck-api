"""
Language-specific special processing registry.

Provides a centralized registry for language-specific text processing functions.
Each language defines its own special processing logic.
"""

from lib.languages import crk, crgn, otwc, otwr, ciw

_languages = {
    'crk': crk,
    'crgn': crgn,
    'otwc': otwc,
    'otwr': otwr,
    'ciw': ciw,
}


def get_language_processor(language_code):
    """
    Get the special processor for a given language code.

    Returns the language module or None if not found.
    """
    if not language_code or not isinstance(language_code, str):
        return None

    return _languages.get(language_code)


def has_fst_file(language_code, fst_type):
    """
    Check if a language has a specific FST file type.

    fst_type: 'strict-analyzer', 'relaxed-analyzer', or 'strict-generator'
    """
    processor = get_language_processor(language_code)
    return bool(processor and hasattr(processor, 'FST_FILES') and processor.FST_FILES.get(fst_type))

"""Tests for lib/special_processing.py and language modules."""

from lib import special_processing
from lib.languages import crk, crgn, otwc, otwr, ciw


class TestGetLanguageProcessor:
    def test_crk_returns_module(self):
        assert special_processing.get_language_processor('crk') is crk

    def test_crgn_returns_module(self):
        assert special_processing.get_language_processor('crgn') is crgn

    def test_otwc_returns_module(self):
        assert special_processing.get_language_processor('otwc') is otwc

    def test_otwr_returns_module(self):
        assert special_processing.get_language_processor('otwr') is otwr

    def test_ciw_returns_module(self):
        assert special_processing.get_language_processor('ciw') is ciw

    def test_unknown_language_returns_none(self):
        assert special_processing.get_language_processor('xyz') is None

    def test_none_returns_none(self):
        assert special_processing.get_language_processor(None) is None

    def test_empty_string_returns_none(self):
        assert special_processing.get_language_processor('') is None


class TestHasFstFile:
    def test_crk_has_strict_analyzer(self):
        assert special_processing.has_fst_file('crk', 'strict-analyzer')

    def test_crk_has_relaxed_analyzer(self):
        assert special_processing.has_fst_file('crk', 'relaxed-analyzer')

    def test_crk_has_strict_generator(self):
        assert special_processing.has_fst_file('crk', 'strict-generator')

    def test_ciw_has_generator(self):
        assert special_processing.has_fst_file('ciw', 'strict-generator')

    def test_otwc_has_generator(self):
        assert special_processing.has_fst_file('otwc', 'strict-generator')

    def test_unknown_language(self):
        assert not special_processing.has_fst_file('xyz', 'strict-analyzer')


class TestCrkProcessCharacters:
    def test_macron_a_to_circumflex(self):
        assert crk.process_characters('ā') == 'â'

    def test_macron_i_to_circumflex(self):
        assert crk.process_characters('ī') == 'î'

    def test_macron_o_to_circumflex(self):
        assert crk.process_characters('ō') == 'ô'

    def test_macron_e_to_circumflex(self):
        assert crk.process_characters('ē') == 'ê'

    def test_strips_punctuation(self):
        assert crk.process_characters('word.') == 'word'
        assert crk.process_characters('word,') == 'word'

    def test_strips_trailing_whitespace(self):
        assert crk.process_characters('  word  ') == 'word'

    def test_none_returns_none(self):
        assert crk.process_characters(None) is None

    def test_empty_returns_empty(self):
        assert crk.process_characters('') == ''

    def test_combined(self):
        assert crk.process_characters('itwēw.') == 'itwêw'


class TestOtwcProcessCharacters:
    def test_strips_punctuation(self):
        assert otwc.process_characters('word.') == 'word'

    def test_no_macron_conversion(self):
        # OTWC does not convert macrons
        assert otwc.process_characters('āword') == 'āword'

    def test_none_returns_none(self):
        assert otwc.process_characters(None) is None

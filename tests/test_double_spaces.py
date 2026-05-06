import pytest
from src.utils import normalize_whitespace, parse_hebrew_date, hebrew_to_civil
from src.name_parser import NameParser

def test_normalize_whitespace():
    assert normalize_whitespace("  hello   world  ") == "hello world"
    assert normalize_whitespace("שניאור  זלמן") == "שניאור זלמן"
    assert normalize_whitespace(None) is None

def test_name_parser_double_spaces():
    parser = NameParser()
    res = parser.parse_name("  שניאור   זלמן   [מלאדי]  ")
    assert res["first_name"] == "שניאור זלמן"
    assert res["last_name"] == "מלאדי"

def test_date_parsing_double_spaces():
    # parse_hebrew_date uses split() which already handles double spaces
    res = parse_hebrew_date("ט'  בכסלו   תרנ\"ד")
    assert res["day"] == 9
    assert res["month"] == 9
    assert res["year"] == 5654

    assert hebrew_to_civil("ט'  בכסלו   תרנ\"ד") == "18 Nov 1893"

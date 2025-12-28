import pytest
from src.utils import hebrew_to_civil, parse_hebrew_date, gematria_to_int

def test_gematria_to_int():
    assert gematria_to_int('א') == 1
    assert gematria_to_int('תשפ"ד') == 784
    assert gematria_to_int('תרנ"ד') == 654
    assert gematria_to_int('ט') == 9

def test_parse_hebrew_date():
    # Full date
    res = parse_hebrew_date('ט\' בכסלו תרנ"ד')
    assert res["day"] == 9
    assert res["month"] == 9
    assert res["year"] == 5654
    
    # Month and year
    res = parse_hebrew_date('כסלו תרנ"ד')
    assert res["day"] is None
    assert res["month"] == 9
    assert res["year"] == 5654
    
    # Only year
    res = parse_hebrew_date('תרנ"ד')
    assert res["day"] is None
    assert res["month"] is None
    assert res["year"] == 5654

def test_hebrew_to_civil():
    # 9 Kislev 5654 -> 18 Nov 1893
    assert hebrew_to_civil('ט\' בכסלו תרנ"ד') == "18 Nov 1893"
    
    # Year only
    # 1 Tishrei 5784 -> 16 Sep 2023
    assert hebrew_to_civil('תשפ"ד') == "2023"
    
    # Month year
    # 1 Kislev 5784 -> 14 Nov 2023
    assert hebrew_to_civil('כסלו תשפ"ד') == "NOV 2023"

def test_gregorian_input():
    assert hebrew_to_civil('1745') == "1745"

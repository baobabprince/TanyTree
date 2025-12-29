import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.name_parser import NameParser

@pytest.fixture
def parser():
    return NameParser()

def test_simple_name(parser):
    name = "יוסף כהן"
    result = parser.parse_name(name)
    assert result["first_name"] == "יוסף"
    assert result["last_name"] == "כהן"

def test_name_with_title(parser):
    name = 'הרבנית הצדקנית מרת רבקה ע"ה [סגל]'
    result = parser.parse_name(name)
    assert result["first_name"] == "רבקה"
    assert result["last_name"] == "סגל"

def test_locational_name(parser):
    name = 'רבנו הגדול בעל התניא והשולחן ערוך רבי שניאור זלמן מליאדי זי"ע'
    result = parser.parse_name(name)
    assert result["first_name"] == "שניאור זלמן"
    assert result["last_name"] == "מליאדי"

def test_single_name(parser):
    name = "משה"
    result = parser.parse_name(name)
    assert result["first_name"] == "משה"
    assert result["last_name"] is None

def test_name_with_multiple_titles(parser):
    name = 'כ"ק אדמו"ר רבי יוסף יצחק'
    result = parser.parse_name(name)
    assert result["first_name"] == "יוסף יצחק"
    assert result["last_name"] is None

def test_empty_name(parser):
    name = ""
    result = parser.parse_name(name)
    assert result["first_name"] == ""
    assert result["last_name"] is None

def test_name_with_only_titles(parser):
    name = 'הרה"ק רבי'
    result = parser.parse_name(name)
    assert result["first_name"] == ""
    assert result["last_name"] is None

def test_another_locational_name(parser):
    name = 'כ"ק אדמו"ר האמצעי רבי דובער מליובאוויטש זי"ע'
    result = parser.parse_name(name)
    assert result["first_name"] == "דובער"
    assert result["last_name"] == "מליובאוויטש"

def test_name_with_middle_name(parser):
    # If not a known double name and no other indicator, it defaults to last word as surname
    name = "רבי אברהם חיים אליהו"
    result = parser.parse_name(name)
    assert result["first_name"] == "אברהם חיים"
    assert result["last_name"] == "אליהו"

def test_female_name_with_one_title(parser):
    name = "מרת שרה"
    result = parser.parse_name(name)
    assert result["first_name"] == "שרה"
    assert result["last_name"] is None

def test_patronymic(parser):
    name = "משה בן עמרם"
    result = parser.parse_name(name)
    assert result["first_name"] == "משה"
    assert result["last_name"] == "בן עמרם"

def test_gender_detection(parser):
    assert parser.detect_gender("רבי יוסף") == "M"
    assert parser.detect_gender("מרת רבקה") == "F"
    assert parser.detect_gender("משה בן עמרם") == "M"
    assert parser.detect_gender("מרים בת עמרם") == "F"

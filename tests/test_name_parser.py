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
    assert result == {"first_name": "יוסף", "last_name": "כהן"}

def test_name_with_title(parser):
    name = 'הרבנית הצדקנית מרת רבקה ע"ה [סגל]'
    result = parser.parse_name(name)
    assert result == {"first_name": "רבקה", "last_name": "סגל"}

def test_locational_name(parser):
    name = 'רבנו הגדול בעל התניא והשולחן ערוך רבי שניאור זלמן מליאדי זי"ע'
    result = parser.parse_name(name)
    assert result == {"first_name": "שניאור זלמן", "last_name": "מליאדי"}

def test_single_name(parser):
    name = "משה"
    result = parser.parse_name(name)
    assert result == {"first_name": "משה", "last_name": None}

def test_name_with_multiple_titles(parser):
    name = 'כ"ק אדמו"ר רבי יוסף יצחק'
    result = parser.parse_name(name)
    assert result == {"first_name": "יוסף", "last_name": "יצחק"}

def test_empty_name(parser):
    name = ""
    result = parser.parse_name(name)
    assert result == {"first_name": "", "last_name": None}

def test_name_with_only_titles(parser):
    name = 'הרה"ק רבי'
    result = parser.parse_name(name)
    assert result == {"first_name": "", "last_name": None}

def test_additional_name_with_title(parser):
    name = 'הרבנית הצדקנית מרת רבקה ע"ה [סגל]'
    result = parser.parse_name(name)
    assert result == {"first_name": "רבקה", "last_name": "סגל"}

def test_another_locational_name(parser):
    name = 'כ"ק אדמו"ר האמצעי רבי דובער מליובאוויטש זי"ע'
    result = parser.parse_name(name)
    assert result == {"first_name": "האמצעי דובער", "last_name": "מליובאוויטש"}

def test_name_with_middle_name(parser):
    name = "רבי אברהם חיים אליהו"
    result = parser.parse_name(name)
    assert result == {"first_name": "אברהם חיים", "last_name": "אליהו"}

def test_female_name_with_one_title(parser):
    name = "מרת שרה"
    result = parser.parse_name(name)
    assert result == {"first_name": "שרה", "last_name": None}

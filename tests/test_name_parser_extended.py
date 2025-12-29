import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.name_parser import NameParser

@pytest.fixture
def parser():
    return NameParser()

def test_name_with_prefix(parser):
    name = "הרה\"ק רבי שמואל"
    result = parser.parse_name(name)
    # Prefix should be captured
    assert result["prefix"] == "הרה\"ק רבי"
    assert result["first_name"] == "שמואל"
    assert result["last_name"] is None

def test_name_with_maiden_in_brackets(parser):
    name = "הרבנית הצדקנית מרת רבקה ע\"ה [סגל]"
    result = parser.parse_name(name)
    assert result["first_name"] == "רבקה"
    assert result["last_name"] == "סגל"
    # Prefix should capture everything before the name
    assert "הרבנית הצדקנית מרת" in result["prefix"]

def test_name_with_trailing_description(parser):
    name = "הרה\"ק רבי שלום דובער - האדמו\"ר מהורש\"א"
    result = parser.parse_name(name)
    assert result["first_name"] == "שלום דובער"
    assert result["last_name"] is None
    assert "האדמו\"ר מהורש\"א" in result["prefix"] or result["suffix"] # Depending on how we implement

def test_name_with_locational_and_prefix(parser):
    name = "רבי שניאור זלמן מליאדי"
    result = parser.parse_name(name)
    assert result["prefix"] == "רבי"
    assert result["first_name"] == "שניאור זלמן"
    assert result["last_name"] == "מליאדי"

def test_complex_honorifics(parser):
    name = "כ\"ק אדמו\"ר האמצעי רבי דובער"
    result = parser.parse_name(name)
    assert "כ\"ק אדמו\"ר האמצעי רבי" in result["prefix"]
    assert result["first_name"] == "דובער"

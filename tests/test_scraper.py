import pytest
from src.scraper import Scraper

@pytest.fixture
def sample_html():
    return """
    <div class="current-view">
        <ul class="parents">
            <li><a href="?i=111813" class="male"><h3>ברוך</h3></a></li>
        </ul>
        <div class="person male">
            <div class="info">
                <h2>שניאור זלמן</h2>
                <h4><a href="?i=111820">סטערנא</a></h4>
                <ul>
                    <li><strong>תאריך לידה: </strong>1745</li>
                    <li><strong>תאריך פטירה: </strong>1812</li>
                </ul>
            </div>
        </div>
        <ul class="kids">
            <li><a href="?i=111821" class="female"><h3>פריידא</h3></a></li>
        </ul>
    </div>
    """

def test_extract_individual_data(sample_html):
    scraper = Scraper()
    data = scraper.extract_biographical_data(sample_html, url="http://example.com/?i=111815")
    
    assert data["id"] == "111815"
    assert "שניאור זלמן" in data["name"]
    assert data["first_name"] == "שניאור זלמן"
    assert data["last_name"] is None
    assert data["birth_date"] == "1745"
    assert data["birth_date_civil"] == "1745"
    assert data["gender"] == "M"

def test_extract_individual_with_prefix_and_maiden():
    html = """
    <div class="person female">
        <div class="info">
            <h2>הרבנית הצדקנית מרת רבקה ע"ה [סגל]</h2>
        </div>
    </div>
    """
    scraper = Scraper()
    data = scraper.extract_biographical_data(html, url="http://example.com/?i=111814")
    
    assert data["first_name"] == "רבקה"
    assert data["last_name"] == "סגל"
    assert "הרבנית" in data["prefix"]
    assert data["gender"] == "F"

def test_extract_individual_with_suffix():
    html = """
    <div class="person male">
        <div class="info">
            <h2>הרה"ק רבי שלום דובער - האדמו"ר מהורש"א</h2>
        </div>
    </div>
    """
    scraper = Scraper()
    data = scraper.extract_biographical_data(html, url="http://example.com/?i=111822")
    
    assert data["first_name"] == "שלום דובער"
    assert data["prefix"] == "הרה\"ק רבי"
    assert data["suffix"] == "האדמו\"ר מהורש\"א"
    assert data["gender"] == "M"

def test_extract_relationships(sample_html):
    scraper = Scraper()
    rels = scraper.extract_relationships(sample_html, person_id="111815")
    
    assert {"person_id": "111815", "related_id": "111813", "type": "father", "url": "?i=111813"} in rels
    assert {"person_id": "111815", "related_id": "111820", "type": "spouse", "url": "?i=111820"} in rels
    assert {"person_id": "111815", "related_id": "111821", "type": "child", "url": "?i=111821"} in rels

def test_extract_relationships_empty():
    scraper = Scraper()
    rels = scraper.extract_relationships("<html><body></body></html>", person_id="111815")
    assert rels == []
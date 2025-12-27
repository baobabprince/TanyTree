import pytest
from src.scraper import Scraper

@pytest.fixture
def sample_html():
    return """
    <html>
        <body>
            <div class="person-name">אדמו"ר הזקן - רבי שניאור זלמן</div>
            <div class="birth-date">י"ח אלול ה'תק"ה</div>
            <div class="death-date">כ"ד טבת ה'תקע"ג</div>
            <div class="gender">זכר</div>
        </body>
    </html>
    """

def test_extract_individual_data(sample_html):
    scraper = Scraper()
    data = scraper.extract_biographical_data(sample_html, url="http://example.com/person1")
    
    assert data["id"] == "person1"
    assert "שניאור זלמן" in data["name"]
    assert data["birth_date"] == 'י"ח אלול ה\'תק"ה'
def test_extract_relationships(sample_html):
    html_with_rels = sample_html + """
    <div class="relationships">
        <div class="father"><a href="/person2">אביו: רבי ברוך</a></div>
        <div class="mother"><a href="/person3">אמו: רבקה</a></div>
        <div class="spouse"><a href="/person4">רעייתו: סטערנא</a></div>
        <div class="children">
            <a href="/person5">דובער</a>
            <a href="/person6">חיים אברהם</a>
            <a href="/person7">משה</a>
        </div>
    </div>
    """
    scraper = Scraper()
    rels = scraper.extract_relationships(html_with_rels, person_id="person1")
    
    assert {"person_id": "person1", "related_id": "person2", "type": "father"} in rels
    assert {"person_id": "person1", "related_id": "person3", "type": "mother"} in rels
    assert {"person_id": "person1", "related_id": "person4", "type": "spouse"} in rels
    assert {"person_id": "person1", "related_id": "person5", "type": "child"} in rels
    assert {"person_id": "person1", "related_id": "person6", "type": "child"} in rels
    assert {"person_id": "person1", "related_id": "person7", "type": "child"} in rels

def test_extract_relationships_empty():
    scraper = Scraper()
    rels = scraper.extract_relationships("<html><body></body></html>", person_id="person1")
    assert rels == []

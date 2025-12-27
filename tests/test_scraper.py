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
    assert data["death_date"] == 'כ"ד טבת ה\'תקע"ג'
    assert data["gender"] == "זכר"
    assert data["url"] == "http://example.com/person1"

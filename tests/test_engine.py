import pytest
from unittest.mock import MagicMock, patch
from src.engine import ScraperEngine
from src.database import DatabaseHelper

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "test.db"
    return DatabaseHelper(str(db_path))

@pytest.fixture
def sample_html():
    return """
    <html>
        <body>
            <div class="person-name">שניאור זלמן</div>
            <div class="birth-date">1745</div>
            <div class="gender">זכר</div>
            <div class="relationships">
                <div class="father"><a href="/p2">ברוך</a></div>
            </div>
        </body>
    </html>
    """

def test_scrape_and_store(mock_db, sample_html):
    with patch("requests.get") as mock_get:
        mock_get.return_value.text = sample_html
        mock_get.return_value.status_code = 200
        
        engine = ScraperEngine(mock_db)
        engine.scrape_person("http://example.com/p1")
        
        # Verify individual stored
        person = mock_db.get_individual("p1")
        assert person["name"] == "שניאור זלמן"
        assert person["id"] == "p1"
        
        # Verify relationship stored
        rels = mock_db.get_relationships("p1")
        assert len(rels) == 1
        assert rels[0]["related_id"] == "p2"
        assert rels[0]["type"] == "father"

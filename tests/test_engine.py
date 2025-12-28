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
    <div class="current-view">
        <div class="person male">
            <div class="info">
                <h2>שניאור זלמן</h2>
                <ul>
                    <li><strong>תאריך לידה: </strong>1745</li>
                </ul>
            </div>
        </div>
        <ul class="parents">
            <li><a href="?i=p2" class="male"><h3>ברוך</h3></a></li>
        </ul>
    </div>
    """

def test_scrape_and_store(mock_db, sample_html):
    with patch("requests.Session.get") as mock_get:
        mock_get.return_value.text = sample_html
        mock_get.return_value.status_code = 200
        
        engine = ScraperEngine(mock_db)
        engine.scrape_person("http://example.com/?i=p1")
        
        # Verify individual stored
        person = mock_db.get_individual("p1")
        assert person["name"] == "שניאור זלמן"
        assert person["id"] == "p1"
        
        # Verify relationship stored
        rels = mock_db.get_relationships("p1")
        assert len(rels) == 1
        assert rels[0]["related_id"] == "p2"
        assert rels[0]["type"] == "father"
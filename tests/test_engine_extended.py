import pytest
from unittest.mock import MagicMock, patch
import requests
from src.engine import ScraperEngine
from src.database import DatabaseHelper
import time

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "test_engine_ext.db"
    return DatabaseHelper(str(db_path))

def test_discover_from_db(mock_db):
    # Setup: one person with a relationship to an unknown person
    mock_db.add_individual({
        "id": "p1", "name": "Parent", "first_name": "Parent", "last_name": "",
        "prefix": None, "suffix": None, "birth_date": None, "birth_date_civil": None,
        "birth_place": None, "death_date": None, "death_date_civil": None,
        "death_place": None, "gender": "M", "url": "http://example.com/?i=p1"
    })
    mock_db.add_relationship("p1", "p2", "child")
    # p2 is NOT in individuals and NOT in discovered_urls

    engine = ScraperEngine(mock_db)
    added = engine._discover_from_db(limit=10)

    assert added == 1
    # Verify p2 is now in discovered_urls
    pending = mock_db.get_pending_urls()
    assert any(p["id"] == "p2" for p in pending)
    assert any(p["url"] == "http://example.com/?i=p2" for p in pending)

def test_crawl_resume_already_visited(mock_db):
    # Setup: p1 is already visited
    mock_db.add_individual({
        "id": "111815", "name": "Root", "first_name": "Root", "last_name": "",
        "prefix": None, "suffix": None, "birth_date": None, "birth_date_civil": None,
        "birth_place": None, "death_date": None, "death_date_civil": None,
        "death_place": None, "gender": "M", "url": "http://example.com/?i=111815"
    })

    engine = ScraperEngine(mock_db, delay=0)

    with patch("requests.Session.get") as mock_get:
        # Mock response for p1 that contains a neighbor p2
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.text = """
        <html><body>
        <div class="person male">
            <div class="info"><h2>Root</h2></div>
            <div class="kids"><ul><li><a href="?i=111816">Child</a></li></ul></div>
        </div>
        </body></html>
        """

        # Also need a response for the neighbor p2 when the queue starts processing
        mock_res2 = MagicMock()
        mock_res2.status_code = 200
        mock_res2.text = '<div class="person"><div class="info"><h2>Child</h2></div></div>'

        # 1. _scrape_one(start_url)
        # 2. crawl's else branch: self.session.get(start_url)
        # 3. _process_queue -> _scrape_one(neighbor_url)
        mock_get.side_effect = [mock_res, mock_res, mock_res2]

        engine.crawl("http://example.com/?i=111815", limit=2)

        # Should have explored p2
        assert "111816" in engine.visited_ids
        assert mock_db.get_individual("111816") is not None

def test_retry_failed_no_pending(mock_db):
    engine = ScraperEngine(mock_db)
    # Should not crash and should print a message
    with patch("builtins.print") as mock_print:
        engine.retry_failed()
        mock_print.assert_any_call("No pending/failed URLs to retry.")

def test_scrape_one_empty_response(mock_db):
    engine = ScraperEngine(mock_db, delay=0)
    with patch("requests.Session.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.text = "" # Empty
        mock_get.return_value = mock_res

        # Currently it does NOT retry on empty response, just returns None
        result = engine._scrape_one("http://example.com/?i=p1")
        assert result is None
        assert mock_get.call_count == 1

def test_scrape_one_generic_exception(mock_db):
    engine = ScraperEngine(mock_db, delay=0)
    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = Exception("Boom")

        result = engine._scrape_one("http://example.com/?i=p1")
        assert result is None
        # Generic exceptions don't retry in the current implementation's outer try-except
        assert mock_get.call_count == 1

def test_scrape_one_connection_error_exhausted(mock_db):
    engine = ScraperEngine(mock_db, delay=0)
    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed")

        result = engine._scrape_one("http://example.com/?i=p1")
        assert result is None
        assert mock_get.call_count == 4 # Initial + 3 retries

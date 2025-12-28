import pytest
from unittest.mock import MagicMock, patch
import requests
from src.engine import ScraperEngine
from src.database import DatabaseHelper
import time

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "test_retries.db"
    return DatabaseHelper(str(db_path))

def test_retries_on_429(mock_db):
    with patch("requests.Session.get") as mock_get:
        # Mock 429 then 200
        mock_429 = MagicMock()
        mock_429.status_code = 429
        
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.text = '<div class="person"><div class="info"><h2>Test</h2></div></div>'
        
        mock_get.side_effect = [mock_429, mock_200]
        
        engine = ScraperEngine(mock_db, delay=0)
        # We need to mock time.sleep to speed up tests
        with patch("time.sleep"):
            result = engine._scrape_one("http://example.com/?i=p1")
        
        assert result is not None
        assert mock_get.call_count == 2

def test_max_retries_exceeded(mock_db):
    with patch("requests.Session.get") as mock_get:
        # Mock 429 consistently
        mock_429 = MagicMock()
        mock_429.status_code = 429
        
        mock_get.return_value = mock_429
        
        engine = ScraperEngine(mock_db, delay=0)
        with patch("time.sleep"):
            result = engine._scrape_one("http://example.com/?i=p1")
        
        assert result is None
        # Initial call + 1 retry = 2 calls
        assert mock_get.call_count == 2

def test_retry_on_timeout(mock_db):
    with patch("requests.Session.get") as mock_get:
        # Mock Timeout then 200
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.text = '<div class="person"><div class="info"><h2>Test</h2></div></div>'
        
        mock_get.side_effect = [requests.exceptions.Timeout("Timeout"), mock_200]
        
        engine = ScraperEngine(mock_db, delay=0)
        with patch("time.sleep"):
            result = engine._scrape_one("http://example.com/?i=p1")
        
        assert result is not None
        assert mock_get.call_count == 2

def test_continue_after_failure_in_crawl(mock_db):
    with patch("requests.Session.get") as mock_get:
        # First call succeeds and returns a person with a child
        mock_first = MagicMock()
        mock_first.status_code = 200
        mock_first.text = """
        <div class="person male">
            <div class="info"><h2>Parent</h2></div>
            <ul class="kids"><li><a href="?i=child">Child</a></li></ul>
        </div>
        """
        
        # Second call (for child) fails
        mock_second = MagicMock()
        mock_second.status_code = 500
        
        mock_get.side_effect = [mock_first, mock_second, mock_second] # 2nd call + 1 retry
        
        engine = ScraperEngine(mock_db, delay=0, max_workers=1)
        with patch("time.sleep"):
            # Crawl with limit 2
            engine.crawl("http://example.com/?i=parent", limit=2)
            
        # Parent should be in DB, child should not (due to failure)
        assert mock_db.get_individual("parent") is not None
        assert mock_db.get_individual("child") is None
        # Total individuals scraped: 1

def test_retry_failed_mechanism(mock_db):
    # Manually add a discovered URL that isn't in individuals
    mock_db.add_discovered_url("p3", "http://example.com/?i=p3")
    
    with patch("requests.Session.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.text = '<div class="person"><div class="info"><h2>Retried</h2></div></div>'
        mock_get.return_value = mock_res
        
        engine = ScraperEngine(mock_db, delay=0)
        engine.retry_failed(limit=10)
        
        assert mock_db.get_individual("p3") is not None
        assert mock_get.call_count == 1

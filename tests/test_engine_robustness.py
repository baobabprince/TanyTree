import pytest
from unittest.mock import MagicMock, patch
import requests
from src.engine import ScraperEngine
from src.database import DatabaseHelper
import time

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "test_robustness.db"
    return DatabaseHelper(str(db_path))

def test_exponential_backoff_and_jitter_on_5xx(mock_db):
    with patch("requests.Session.get") as mock_get, patch("time.sleep") as mock_sleep:
        # Mock two 500 errors then a 200 OK
        mock_500 = MagicMock()
        mock_500.status_code = 500

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.text = '<div class="person"><div class="info"><h2>Robust Test</h2></div></div>'

        mock_get.side_effect = [mock_500, mock_500, mock_200]

        engine = ScraperEngine(mock_db, delay=0)
        result = engine._scrape_one("http://example.com/?i=robust1")

        assert result is not None
        assert mock_get.call_count == 3
        # mock_sleep called for each retry (attempt 0 and 1)
        # and also for self.delay (which is 0, so maybe not called or called with 0)
        # In _request_with_retry: if self.delay > 0: time.sleep(self.delay) -> not called
        # Then after 429/500: time.sleep(sleep_time) -> called twice
        assert mock_sleep.call_count == 2

        # Check backoff timing
        # 1st retry: 5 * (2**0) + jitter = 5 + jitter
        # 2nd retry: 5 * (2**1) + jitter = 10 + jitter
        calls = [args[0] for args, kwargs in mock_sleep.call_args_list]
        assert 5 <= calls[0] <= 6
        assert 10 <= calls[1] <= 11

def test_persistent_429_max_retries(mock_db):
    with patch("requests.Session.get") as mock_get, patch("time.sleep") as mock_sleep:
        # Consistently return 429
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_get.return_value = mock_429

        engine = ScraperEngine(mock_db, delay=0)
        result = engine._scrape_one("http://example.com/?i=fail429")

        assert result is None
        # 1 initial + 3 retries = 4 attempts
        assert mock_get.call_count == 4
        assert mock_sleep.call_count == 3

def test_connection_error_retries(mock_db):
    with patch("requests.Session.get") as mock_get, patch("time.sleep") as mock_sleep:
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.text = '<div class="person"><div class="info"><h2>Connection Test</h2></div></div>'

        mock_get.side_effect = [requests.exceptions.ConnectionError("Failed"), mock_200]

        engine = ScraperEngine(mock_db, delay=0)
        result = engine._scrape_one("http://example.com/?i=conn1")

        assert result is not None
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1

def test_crawl_skips_visited(mock_db):
    # Pre-populate visited_ids
    mock_db.add_individual({
        "id": "visited1", "name": "Already Visited", "first_name": "Already", "last_name": "Visited",
        "prefix": None, "suffix": None, "birth_date": None, "birth_date_civil": None, "birth_place": None,
        "death_date": None, "death_date_civil": None, "death_place": None, "gender": "M", "url": "http://example.com/?i=visited1"
    })

    with patch("src.engine.ScraperEngine._scrape_one") as mock_scrape, \
         patch("requests.Session.get") as mock_get:

        # Mock resume response for relationships
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.text = '<div class="person"></div>' # No new rels for simplicity
        mock_get.return_value = mock_res

        engine = ScraperEngine(mock_db, delay=0)
        # Need to refresh visited_ids since it was added directly to DB
        engine.visited_ids = set(mock_db.get_all_ids())

        engine.crawl("http://example.com/?i=visited1", limit=1)

        # _scrape_one should NOT be called for visited1
        mock_scrape.assert_not_called()
        # But session.get might be called in the resume logic
        assert mock_get.call_count == 1

import pytest
from click.testing import CliRunner
from src.cli import main
from unittest.mock import patch, MagicMock

@pytest.fixture
def runner():
    return CliRunner()

def test_cli_crawl(runner, tmp_path):
    db_path = tmp_path / "test_crawl.db"
    with patch("src.cli.ScraperEngine") as mock_engine_cls:
        mock_engine = mock_engine_cls.return_value

        result = runner.invoke(main, ["crawl", "--url", "http://example.com/?i=p1", "--db", str(db_path), "--limit", "5"])

        assert result.exit_code == 0
        assert "Crawling starting from" in result.output
        assert "Crawl complete" in result.output
        mock_engine.crawl.assert_called_once()

def test_cli_retry(runner, tmp_path):
    db_path = tmp_path / "test_retry.db"
    with patch("src.cli.ScraperEngine") as mock_engine_cls:
        mock_engine = mock_engine_cls.return_value

        result = runner.invoke(main, ["retry", "--db", str(db_path), "--limit", "10"])

        assert result.exit_code == 0
        assert "Retrying up to 10 pending items" in result.output
        assert "Retry complete" in result.output
        mock_engine.retry_failed.assert_called_once_with(limit=10)

import pytest
from click.testing import CliRunner
from src.cli import main
import os

@pytest.fixture
def runner():
    return CliRunner()

def test_cli_scrape_help(runner):
    result = runner.invoke(main, ["scrape", "--help"])
    assert result.exit_code == 0
    assert "Scrape" in result.output

def test_cli_export_help(runner):
    result = runner.invoke(main, ["export", "--help"])
    assert result.exit_code == 0
    assert "Export" in result.output

def test_cli_full_flow(runner, tmp_path):
    db_path = tmp_path / "test_cli.db"
    output_ged = tmp_path / "output.ged"
    
    # Mock requests for scrape
    from unittest.mock import patch
    sample_html = """
    <html>
        <body>
            <div class="person-name">Test Person</div>
            <div class="birth-date">2000</div>
            <div class="gender">M</div>
        </body>
    </html>
    """
    
    with patch("requests.get") as mock_get:
        mock_get.return_value.text = sample_html
        mock_get.return_value.status_code = 200
        
        # Scrape
        result = runner.invoke(main, ["scrape", "http://example.com/p1", "--db", str(db_path)])
        assert result.exit_code == 0
        assert "Scrape complete" in result.output
        
        # Export
        result = runner.invoke(main, ["export", str(output_ged), "--db", str(db_path)])
        assert result.exit_code == 0
        assert "Export complete" in result.output
        assert os.path.exists(output_ged)
        
        with open(output_ged, "r") as f:
            content = f.read()
            assert "NAME Test Person" in content

import click
import sys
import os

# Add the project root to sys.path to allow running this script directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseHelper
from src.engine import ScraperEngine
from src.gedcom_exporter import GedcomExporter

DEFAULT_URL = "https://baalhatanya.org.il/%d7%90%d7%99%d7%92%d7%95%d7%93-%d7%94%d7%a6%d7%90%d7%a6%d7%90%d7%99%d7%9d-%d7%a9%d7%9c-%d7%91%d7%a2%d7%9c-%d7%94%d7%aa%d7%a0%d7%99%d7%90-%d7%94%d7%90%d7%93%d7%9e%d7%95%d7%a8-%d7%94%d7%96%d7%a7%d7%9f/%d7%90%d7%99%d7%9c%d7%9f-%d7%94%d7%99%d7%97%d7%a1/?i=111815"

@click.group()
def main():
    """Gen genealogical data scraper and GEDCOM exporter."""
    pass

@main.command()
@click.option('--url', default=DEFAULT_URL, help='URL of the person to scrape.')
@click.option('--db', default='genealogy.db', help='Database file path.')
@click.option('--delay', default=1.0, help='Delay between requests in seconds.')
def scrape(url, db, delay):
    """Scrape genealogical data from a URL."""
    db_helper = DatabaseHelper(db)
    engine = ScraperEngine(db_helper, delay=delay)
    click.echo(f"Scraping {url}...")
    engine.scrape_person(url)
    click.echo("Scrape complete.")
    db_helper.close()

@main.command()
@click.option('--url', default=DEFAULT_URL, help='URL to start crawling from.')
@click.option('--limit', default=100, help='Maximum number of people to scrape.')
@click.option('--db', default='genealogy.db', help='Database file path.')
@click.option('--workers', default=2, help='Number of concurrent workers.')
@click.option('--delay', default=1.0, help='Delay between requests in seconds.')
def crawl(url, limit, db, workers, delay):
    """Crawl genealogical data starting from a URL."""
    db_helper = DatabaseHelper(db)
    engine = ScraperEngine(db_helper, max_workers=workers, delay=delay)
    click.echo(f"Crawling starting from {url} with limit {limit} (workers: {workers}, delay: {delay}s)...")
    engine.crawl(url, limit=limit)
    click.echo("Crawl complete.")
    db_helper.close()

@main.command()
@click.option('--limit', default=100, help='Maximum number of people to retry.')
@click.option('--db', default='genealogy.db', help='Database file path.')
@click.option('--workers', default=2, help='Number of concurrent workers.')
@click.option('--delay', default=1.0, help='Delay between requests in seconds.')
def retry(limit, db, workers, delay):
    """Retry failed or pending scrapings."""
    db_helper = DatabaseHelper(db)
    engine = ScraperEngine(db_helper, max_workers=workers, delay=delay)
    click.echo(f"Retrying up to {limit} pending items...")
    engine.retry_failed(limit=limit)
    click.echo("Retry complete.")
    db_helper.close()

@main.command()
@click.argument('output')
@click.option('--db', default='genealogy.db', help='Database file path.')
def export(output, db):
    """Export scraped data to a GEDCOM file."""
    db_helper = DatabaseHelper(db)
    exporter = GedcomExporter(db_helper)
    click.echo(f"Exporting to {output}...")
    exporter.export(output)
    click.echo("Export complete.")
    db_helper.close()

if __name__ == '__main__':
    main()

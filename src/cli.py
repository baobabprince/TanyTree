import click
from src.database import DatabaseHelper
from src.engine import ScraperEngine
from src.gedcom_exporter import GedcomExporter

@click.group()
def main():
    """Gen genealogical data scraper and GEDCOM exporter."""
    pass

@main.command()
@click.argument('url')
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
@click.argument('url')
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

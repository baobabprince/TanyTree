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
def scrape(url, db):
    """Scrape genealogical data from a URL."""
    db_helper = DatabaseHelper(db)
    engine = ScraperEngine(db_helper)
    click.echo(f"Scraping {url}...")
    engine.scrape_person(url)
    click.echo("Scrape complete.")
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

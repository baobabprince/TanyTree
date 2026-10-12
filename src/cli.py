import click
import sys
import os

# Add the project root to sys.path to allow running this script directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseHelper
from src.engine import ScraperEngine
from src.gedcom_exporter import GedcomExporter
from src.change_tracker import ChangeTracker
from src.tree_enricher import TreeEnricher

DEFAULT_URL = "https://baalhatanya.org.il/%d7%90%d7%99%d7%92%d7%95%d7%93-%d7%94%d7%a6%d7%90%d7%a6%d7%90%d7%99%d7%9d-%d7%a9%d7%9c-%d7%91%d7%a2%d7%9c-%d7%94%d7%aa%d7%a0%d7%99%d7%90-%d7%94%d7%90%d7%93%d7%9e%d7%95%d7%a8-%d7%94%d7%96%d7%a7%d7%9f/%d7%90%d7%99%d7%9c%d7%9f-%d7%94%d7%99%d7%a1%d7%a5/?i=111815"

@click.group()
def main():
    """Gen genealogical data scraper and GEDCOM exporter."""
    pass

@main.command()
@click.option('--url', default=DEFAULT_URL, help='URL of the person to scrape.')
@click.option('--db', default='genealogy.db', help='Database file path.')
@click.option('--delay', default=1.0, help='Delay between requests in seconds.')
@click.option('--force', is_flag=True, help='Overwrite existing data.')
@click.option('--report-file', default='changes_summary.md', help='Output summary report file path.')
def scrape(url, db, delay, force, report_file):
    """Scrape genealogical data from a URL."""
    db_helper = DatabaseHelper(db)
    tracker = ChangeTracker(db_helper)
    tracker.take_snapshot()

    engine = ScraperEngine(db_helper, delay=delay)
    if force:
        click.echo(f"Scraping {url} (forced update)...")
    else:
        click.echo(f"Scraping {url}...")
    engine.scrape_person(url, force=force)
    click.echo("Scrape complete.")

    changes = tracker.compute_changes()
    report = tracker.generate_report(changes, output_file=report_file)
    click.echo("\n" + report)

    db_helper.close()

@main.command()
@click.option('--url', default=DEFAULT_URL, help='URL to start crawling from.')
@click.option('--limit', default=100, help='Maximum number of people to scrape.')
@click.option('--db', default='genealogy.db', help='Database file path.')
@click.option('--workers', default=2, help='Number of concurrent workers.')
@click.option('--delay', default=1.0, help='Delay between requests in seconds.')
@click.option('--report-file', default='changes_summary.md', help='Output summary report file path.')
def crawl(url, limit, db, workers, delay, report_file):
    """Crawl genealogical data starting from a URL."""
    db_helper = DatabaseHelper(db)
    tracker = ChangeTracker(db_helper)
    tracker.take_snapshot()

    engine = ScraperEngine(db_helper, max_workers=workers, delay=delay)
    click.echo(f"Crawling starting from {url} with limit {limit} (workers: {workers}, delay: {delay}s)...")
    engine.crawl(url, limit=limit)
    click.echo("Crawl complete.")

    changes = tracker.compute_changes()
    report = tracker.generate_report(changes, output_file=report_file)
    click.echo("\n" + report)

    db_helper.close()

@main.command()
@click.option('--limit', default=100, help='Maximum number of people to retry.')
@click.option('--db', default='genealogy.db', help='Database file path.')
@click.option('--workers', default=2, help='Number of concurrent workers.')
@click.option('--delay', default=1.0, help='Delay between requests in seconds.')
@click.option('--report-file', default='changes_summary.md', help='Output summary report file path.')
def retry(limit, db, workers, delay, report_file):
    """Retry failed or pending scrapings."""
    db_helper = DatabaseHelper(db)
    tracker = ChangeTracker(db_helper)
    tracker.take_snapshot()

    engine = ScraperEngine(db_helper, max_workers=workers, delay=delay)
    click.echo(f"Retrying up to {limit} pending items...")
    engine.retry_failed(limit=limit)
    click.echo("Retry complete.")

    changes = tracker.compute_changes()
    report = tracker.generate_report(changes, output_file=report_file)
    click.echo("\n" + report)

    db_helper.close()

@main.command(name='summary')
@click.option('--db', default='genealogy.db', help='Database file path.')
@click.option('--report-file', default='changes_summary.md', help='Summary report file path to display if available.')
def summary(db, report_file):
    """Display general statistics and latest changes summary of the tree."""
    if os.path.exists(report_file):
        with open(report_file, 'r', encoding='utf-8') as f:
            click.echo(f.read())
    else:
        db_helper = DatabaseHelper(db)
        enricher = TreeEnricher(db_helper)
        q = enricher.quality_report()
        click.echo("# נתונים סטטיסטיים כלליים של עץ היחס")
        click.echo(
            f"- **סה\"כ אנשים בעץ:** {q['total_individuals']} "
            f"({q['gender_M']} זכרים, {q['gender_F']} נקבות, {q['gender_U']} ללא ציון מגדר)"
        )
        click.echo(f"- **קשרי spouse:** {q['spouse_links']}")
        click.echo(f"- **related_ids יתומים (בלי individual):** {q['orphan_related_ids']}")
        click.echo(f"- **אנשים מבודדים (בלי קשרים):** {q['isolated_individuals']}")
        click.echo(f"- **קשרי parent לא מפוענחים:** {q['unresolved_parent_links']}")
        click.echo(f"- **דפים ממתינים לגרידה:** {q['pending_urls']}")
        click.echo(f"- **דפים שנכשלו באופן קבוע (3 ניסיונות+):** {q['failed_urls']}")
        db_helper.close()

@main.command()
@click.option('--db', default='genealogy.db', help='Database file path.')
def enrich(db):
    """Offline: infer genders, canonicalize relationships, discover orphan IDs."""
    db_helper = DatabaseHelper(db)
    enricher = TreeEnricher(db_helper)
    click.echo("Running offline enrichment...")
    result = enricher.enrich()
    click.echo(f"Genders updated: {result['genders_updated']}")
    click.echo(f"Relationships added (bidirectional): {result['relationships_added']}")
    click.echo(f"Parent links resolved to father/mother: {result['parents_resolved']}")
    click.echo(f"Orphan IDs discovered: {result['orphans_discovered']}")
    q = result['quality']
    click.echo("\n# Quality after enrich")
    click.echo(
        f"Individuals: {q['total_individuals']} "
        f"(M={q['gender_M']}, F={q['gender_F']}, U={q['gender_U']})"
    )
    click.echo(f"Orphan related_ids: {q['orphan_related_ids']}")
    click.echo(f"Isolated: {q['isolated_individuals']}")
    click.echo(f"Unresolved parent: {q['unresolved_parent_links']}")
    click.echo(f"Pending URLs: {q['pending_urls']}")
    db_helper.close()

@main.command(name='quality')
@click.option('--db', default='genealogy.db', help='Database file path.')
def quality(db):
    """Show data-quality metrics without modifying the database."""
    db_helper = DatabaseHelper(db)
    enricher = TreeEnricher(db_helper)
    q = enricher.quality_report()
    click.echo("# Data quality")
    for k, v in q.items():
        click.echo(f"- {k}: {v}")
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

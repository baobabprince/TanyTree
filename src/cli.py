import click
import sys
import os

# Add the project root to sys.path to allow running this script directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseHelper
from src.engine import ScraperEngine
from src.gedcom_exporter import GedcomExporter
from src.change_tracker import ChangeTracker

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
        cursor = db_helper.conn.cursor()
        cursor.execute("SELECT * FROM individuals")
        post_inds = {row["id"]: dict(row) for row in cursor.fetchall()}
        cursor.execute("SELECT person_id, related_id, type FROM relationships")
        post_rels = set((row["person_id"], row["related_id"], row["type"]) for row in cursor.fetchall())
        cursor.execute("SELECT id, url, failure_count FROM discovered_urls")
        post_urls = {row["id"]: {"url": row["url"], "failure_count": row["failure_count"]} for row in cursor.fetchall()}

        pending_urls = [u for u_id, u in post_urls.items() if u_id not in post_inds and u["failure_count"] < 3]

        total_individuals = len(post_inds)
        males = sum(1 for p in post_inds.values() if p.get("gender") == "M")
        females = sum(1 for p in post_inds.values() if p.get("gender") == "F")
        unknown_gender = total_individuals - (males + females)
        total_rels = len(post_rels)
        total_failed_urls = sum(1 for u in post_urls.values() if u["failure_count"] >= 3)
        total_pending_urls = len(pending_urls)

        click.echo("# נתונים סטטיסטיים כלליים של עץ היחס")
        click.echo(f"- **סה\"כ אנשים בעץ:** {total_individuals} ({males} זכרים, {females} נקבות, {unknown_gender} ללא ציון מגדר)")
        click.echo(f"- **סה\"כ קשרים משפחתיים בעץ:** {total_rels}")
        click.echo(f"- **דפים ממתינים לגרידה:** {total_pending_urls}")
        click.echo(f"- **דפים שנכשלו באופן קבוע (3 ניסיונות+):** {total_failed_urls}")

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

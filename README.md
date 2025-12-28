# Baal HaTanya Genealogy Scraper

A specialized tool to scrape genealogical data from [baalhatanya.org.il](https://baalhatanya.org.il/) and export it to the standard GEDCOM format. This project is designed to help researchers and genealogists interested in the Chabad dynasty preserve and utilize family tree data in their own genealogy software.

## Features

- **Automated Crawling:** Recursively traverses individual and family pages to build a comprehensive tree.
- **Data Extraction:** Captures names, birth/death dates, locations, and gender.
- **Relationship Mapping:** Automatically links parents, spouses, and children.
- **Hebrew Support:** Specifically designed to handle Hebrew text and cultural context from the source site.
- **GEDCOM Export:** Generates valid GEDCOM files compatible with Gramps, MyHeritage, Ancestry, and other standard software.
- **SQLite Storage:** Uses a local database to store scraped data, allowing for interrupted crawls and incremental updates.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tny
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The project provides a Command Line Interface (CLI) via `src/cli.py`.

### 1. Scrape a Single Person
Extract data for a specific individual using their URL.
```bash
python -m src.cli scrape "https://baalhatanya.org.il/%d7%90%d7%99%d7%92%d7%95%d7%93-%d7%94%d7%a6%d7%90%d7%a6%d7%90%d7%99%d7%9d-%d7%a9%d7%9c-%d7%91%d7%a2%d7%9c-%d7%94%d7%aa%d7%a0%d7%99%d7%90-%d7%94%d7%90%d7%93%d7%9e%d7%95%d7%a8-%d7%94%d7%96%d7%a7%d7%9f/%d7%90%d7%99%d7%9c%d7%9f-%d7%94%d7%99%d7%97%d7%a1/?i=111815"
```

### 2. Crawl the Tree
Start from a specific URL and recursively crawl connected individuals.
```bash
python -m src.cli crawl "https://baalhatanya.org.il/%d7%90%d7%99%d7%92%d7%95%d7%93-%d7%94%d7%a6%d7%90%d7%a6%d7%90%d7%99%d7%9d-%d7%a9%d7%9c-%d7%91%d7%a2%d7%9c-%d7%94%d7%aa%d7%a0%d7%99%d7%90-%d7%94%d7%90%d7%93%d7%9e%d7%95%d7%a8-%d7%94%d7%96%d7%a7%d7%9f/%d7%90%d7%99%d7%9c%d7%9f-%d7%94%d7%99%d7%97%d7%a1/?i=111815" --limit 100
```
- `--limit`: Maximum number of people to crawl (default: 100).
- `--db`: Path to the SQLite database (default: `genealogy.db`).

**Note on URLs:** For the scraper to correctly identify individual pages, ensure the URL includes the full path to the genealogy section (usually containing `%d7%90%d7%99%d7%9c%d7%9f-%d7%94%d7%99%d7%97%d7%a1`) followed by the `?i=ID` parameter. Root IDs typically start around 111815.

### 3. Export to GEDCOM
Convert the stored database records into a GEDCOM file.
```bash
python -m src.cli export genealogy.ged
```

## Project Structure

- `src/`: Core logic
    - `cli.py`: Command-line interface.
    - `scraper.py`: HTML parsing and data extraction logic.
    - `engine.py`: Orchestrates crawling and scraping workflows.
    - `database.py`: Handles SQLite storage.
    - `gedcom_exporter.py`: Converts database records to GEDCOM format.
- `tests/`: Unit tests for each component.
- `requirements.txt`: Python dependencies.

## Testing

Run the test suite using `pytest`:
```bash
pytest
```

## Disclaimer

This tool is for personal and research use only. Please respect the terms of service of the source website and avoid placing excessive load on their servers.

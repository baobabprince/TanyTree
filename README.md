# TanyTree

A specialized tool to scrape genealogical data from [baalhatanya.org.il](https://baalhatanya.org.il/) and export it to the standard GEDCOM format. This project is designed to help researchers and genealogists interested in the Chabad dynasty preserve and utilize family tree data in their own genealogy software.

## Features

- **Automated Crawling:** Recursively traverses individual and family pages to build a comprehensive tree.
- **Data Extraction:** Captures names, birth/death dates, locations, and gender.
- **Relationship Mapping:** Automatically links parents, spouses, and children.
- **Resumable Crawling:** Automatically skips already successfully scraped individuals and tracks discovered but pending URLs.
- **Hebrew Support:** Specifically designed to handle Hebrew text and cultural context from the source site.
- **GEDCOM Export:** Generates valid GEDCOM files compatible with Gramps, MyHeritage, Ancestry, and other standard software.
- **SQLite Storage:** Uses a local database to store scraped data, allowing for interrupted crawls and incremental updates.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd TanyTree
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The project provides a Command Line Interface (CLI) via `src/cli.py`. All commands automatically skip individuals already present in the database.

### 1. Scrape a Single Person
Extract data for a specific individual using their URL.
```bash
python -m src.cli scrape "https://baalhatanya.org.il/.../?i=111815"
```

### 2. Crawl the Tree
Start from a specific URL and recursively crawl connected individuals.
```bash
python -m src.cli crawl "https://baalhatanya.org.il/.../?i=111815" --limit 100
```
- `--limit`: Maximum number of people to crawl (default: 100).
- `--workers`: Number of concurrent workers (default: 2).
- `--delay`: Delay between requests in seconds (default: 1.0).

### 3. Retry Failed/Pending Pages
If a crawl was interrupted or some pages failed due to network errors, use the retry command to attempt them again without re-crawling the entire tree.
```bash
python -m src.cli retry --limit 100
```

### 4. Export to GEDCOM
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

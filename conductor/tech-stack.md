# Tech Stack

## Programming Language
*   **Python 3.10+**: Chosen for its robust ecosystem of scraping libraries, ease of data manipulation, and strong support for CLI development.

## Core Libraries
*   **Requests:** For handling HTTP requests to baalhatanya.org.il.
*   **BeautifulSoup4:** For parsing HTML and extracting genealogical data from the site's pages.
*   **python-gedcom:** For generating valid GEDCOM 5.5.1 files, ensuring compatibility with genealogical software.

## Data Persistence & Caching
*   **SQLite:** Used as a local cache to store scraped individuals, families, and relationships. This allows for incremental scraping, reduces server load, and simplifies the final tree construction.

## Development & Tooling
*   **Pytest:** For unit and integration testing of the scraping and conversion logic.
*   **Black / Flake8:** For code formatting and linting to maintain high code quality.
*   **Click / Argparse:** For building a user-friendly CLI interface.

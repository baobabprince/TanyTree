# Track Spec: Core Scraping and GEDCOM Conversion Engine

## Overview
This track focuses on building the foundational components required to scrape genealogical data from baalhatanya.org.il and convert it into a valid GEDCOM file. It includes setting up the project structure, the local database for caching, the scraper engine, and the GEDCOM export logic.

## Functional Requirements
- **Project Scaffolding:** Set up a Python project with necessary dependencies (Requests, BeautifulSoup4, python-gedcom, SQLite, Pytest).
- **Database Schema:** Define a SQLite schema to store individuals (ID, name, birth date, death date, etc.) and relationships (parent-child, spouse).
- **Basic Scraper:** Implement a scraper that can fetch a single page and extract core biographical data.
- **Relationship Mapping:** Extract and store links between individuals to form family structures.
- **GEDCOM Export:** Implement logic to read from the local database and generate a valid GEDCOM 5.5.1 file.
- **CLI Interface:** Provide basic CLI commands to start the scraping process and trigger the export.

## Non-Functional Requirements
- **Compliance:** Generated GEDCOM files must follow the 5.5.1 specification.
- **Performance:** Efficiently handle data extraction and database writes.
- **Robustness:** Gracefully handle network errors and unexpected HTML structures.

## Acceptance Criteria
- Successful extraction of data for at least 10 individuals and their immediate family members from the site.
- Generation of a valid GEDCOM file containing the extracted data.
- GEDCOM file can be imported into standard genealogy software without errors.
- Automated tests covering the scraper and the GEDCOM generation logic.

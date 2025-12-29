# Product Guide

# Initial Concept

script that scrape https://baalhatanya.org.il/ and convert it to gedcom file

## Target Audience
The primary users are casual researchers and genealogists interested in the Chabad dynasty who want a straightforward way to export family tree data from baalhatanya.org.il into standard GEDCOM format for use in their own genealogy software.

## Goals
*   **Accuracy:** Ensure all genealogical data, including names, dates, and relationships, is correctly mapped from the source website to the GEDCOM 5.5.1 or 7.0 standard.
*   **Simplicity:** Provide a CLI-based tool that is easy to execute with minimal configuration, making it accessible to users with basic technical knowledge.
*   **Performance:** Implement an efficient scraping strategy to navigate the site's structure and extract data without unnecessary delays or server strain.

## Core Features
*   **Automated Web Crawling:** A robust crawler designed to traverse the specific structure of baalhatanya.org.il, identifying and visiting all relevant individual and family pages.
*   **Structured Name Extraction:** Advanced name parsing to separate given names, surnames, and honorifics, including the detection of maiden names in brackets, ensuring high fidelity in GEDCOM exports.
*   **Relationship Mapping:** Comprehensive extraction of family connections, including parents, spouses, and children, to reconstruct a complete and interconnected family tree.
*   **Biographical Data Extraction:** Capture of birth and death dates, locations, and any available historical notes or descriptions provided on the site.

## Success Criteria
*   Generation of a valid GEDCOM file that passes standard syntax validation.
*   Successful import of the generated file into popular genealogy software (e.g., Gramps, MyHeritage, Ancestry).
*   High fidelity of the exported data compared to the source website.

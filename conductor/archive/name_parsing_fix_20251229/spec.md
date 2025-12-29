# Specification: Name Parsing and GEDCOM Tagging Bug Fix

## Overview
The current implementation fails to distinguish between given names and surnames, and does not capture birth names for women. This track will implement a robust name parser to correctly identify given names, surnames (including birth names marked in brackets `[]`), and honorifics, ensuring they are exported with the correct structured GEDCOM tags.

## Functional Requirements
1.  **Enhanced Name Parsing:**
    *   **Structure:** Separate full name strings into "Given Name" and "Surname".
    *   **Birth Names:** Specifically detect birth names for women, which are typically enclosed in brackets (e.g., "First Last [BirthName]").
    *   **Honorifics:** Recognize and handle common Hebrew honorifics (e.g., "Rabbi", "HaRav", "Admor"). These should be stripped from the `GIVN`/`SURN` tags and ideally placed in `NPFX`.
    *   **Complex Names:** Handle multi-word surnames and patronymics common in the Chabad dynasty.
2.  **Structured GEDCOM Output:**
    *   **Standard Name Line:** Export `1 NAME <Given> /<Surname>/`.
    *   **Subordinate Tags:** Include `2 GIVN <Given>` and `2 SURN <Surname>`.
    *   **Maiden Name:** For women with a detected birth name, use the birth name in the `SURN` tag and the `1 NAME` line, or use the appropriate GEDCOM structure for multiple names if preferred (defaulting to birth name as the primary surname).
3.  **Source Integration:**
    *   Improve extraction logic to parse these details from single-string HTML elements on baalhatanya.org.il.

## Non-Functional Requirements
*   **Accuracy:** High precision in identifying birth names within brackets.
*   **Clean Slate:** Backward compatibility is NOT required; a full re-scrape will be performed.

## Acceptance Criteria
*   [ ] Unit tests verify correct parsing of:
    *   Simple names (First Last)
    *   Names with honorifics (Rabbi First Last)
    *   Women's names with birth names (First Last [Maiden])
*   [ ] GEDCOM export includes `1 NAME`, `2 GIVN`, and `2 SURN` tags.
*   [ ] Birth names are correctly identified and placed in the surname field.

## Out of Scope
*   Maintaining or migrating old data from the current `genealogy.db`.

# Plan: Name Parsing and GEDCOM Tagging Bug Fix

## Phase 1: Research and Analysis [checkpoint: phase1]
- [x] Task: Review existing `NameParser` regex and title lists to identify missing honorifics and birth name patterns.
- [x] Task: Analyze current `GedcomExporter` implementation to prepare for subordinate tag integration.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Research and Analysis' (Protocol in workflow.md)

## Phase 2: Name Parser Enhancements (TDD) [checkpoint: phase2]
- [x] Task: [RED] Create `tests/test_name_parser_extended.py` with cases for honorifics, patronymics, and bracketed birth names.
- [x] Task: [GREEN] Update `src/name_parser.py` to correctly extract given names, surnames, and birth names.
- [x] Task: [REFACTOR] Clean up parsing logic and ensure the `detect_gender` method is robust.
- [x] Task: [RED] Add tests for honorific stripping (e.g., "Rabbi" -> `NPFX`).
- [x] Task: [GREEN] Implement honorific stripping and storage in the parser result.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Name Parser Enhancements' (Protocol in workflow.md)

## Phase 3: GEDCOM Exporter Updates (TDD) [checkpoint: phase3]
- [x] Task: [RED] Update `tests/test_gedcom.py` to assert the presence of `2 GIVN`, `2 SURN`, and potentially `2 NPFX` tags.
- [x] Task: [GREEN] Modify `src/gedcom_exporter.py` to include structured subordinate tags in the export.
- [x] Task: [REFACTOR] Ensure name formatting in `1 NAME` line follows the `Given /Surname/` standard.
- [x] Task: Conductor - User Manual Verification 'Phase 3: GEDCOM Exporter Updates' (Protocol in workflow.md)

## Phase 4: Scraper and Database Integration (TDD) [checkpoint: phase4]
- [x] Task: [RED] Update `tests/test_scraper.py` to ensure birth names and honorifics are correctly extracted from HTML.
- [x] Task: [GREEN] Update `src/scraper.py` and `src/database.py` (if schema changes are needed) to store and pass extended name data.
- [x] Task: [REFACTOR] Optimize scraper extraction logic for improved reliability on single-string elements.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Scraper and Database Integration' (Protocol in workflow.md)

## Phase 5: End-to-End Verification [checkpoint: phase5]
- [x] Task: Run a full scrape of a representative subset of the website.
- [x] Task: Export the results to GEDCOM and validate the structure using an external validator (e.g., Gramps).
- [x] Task: Verify that birth names for women are correctly placed in the surname field.
- [x] Task: Conductor - User Manual Verification 'Phase 5: End-to-End Verification' (Protocol in workflow.md)

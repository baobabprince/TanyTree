# Product Guidelines

## Prose Style
*   **Tone:** Helpful and instructive. Communication should be clear, concise, and accessible to a non-technical audience.
*   **Language:** Primary output in Hebrew (matching the source material), with secondary English for CLI instructions and status messages.
*   **Terminology:** Use standard genealogical terms (e.g., "Sons," "Daughters," "Spouse," "Birth Date") to ensure familiarity for the target audience.

## User Interface (CLI)
*   **Progress Indicators:** Provide clear visual feedback (e.g., progress bars, item counts) during the scraping and conversion process.
*   **Error Messages:** Present user-friendly error messages that suggest corrective actions where possible (e.g., "Please check your internet connection" instead of a raw stack trace).
*   **Help Commands:** Include a clear --help flag with detailed instructions on how to use the script.

## Data Quality & Integrity
*   **Standardization:** Adhere strictly to the GEDCOM 5.5.1 specification to ensure maximum compatibility with other software.
*   **Preservation:** Maintain the original Hebrew names as the primary identifier, while offering options for transliteration if requested.
*   **Traceability:** Include a "Source" field in the GEDCOM file pointing to the specific URL on baalhatanya.org.il where the data was found.

## Performance & Ethics
*   **Politeness:** Implement request rate-limiting to avoid overwhelming the target website's servers.
*   **Caching:** Use a local cache for scraped pages to speed up subsequent runs and reduce redundant network traffic.

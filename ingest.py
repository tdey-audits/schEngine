#!/usr/bin/env python3
"""Run the NCERT PDF ingestion pipeline."""

import logging

from ingest.pipeline import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if __name__ == "__main__":
    count = run_ingestion()
    if count:
        print(f"\nIngested {count} chunks from NCERT PDFs into FAISS.")
    else:
        print("\nNo chunks ingested. Check that PDFs exist in ncert_maths_chapters/")

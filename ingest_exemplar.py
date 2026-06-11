#!/usr/bin/env python3
"""Run the NCERT Exemplar ingestion pipeline."""

import logging

from ingest.exemplar_pipeline import run_exemplar_ingestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


if __name__ == "__main__":
    count = run_exemplar_ingestion()
    if count:
        print(f"\nIngested {count} NCERT Exemplar question chunks into the Exemplar FAISS corpus.")
    else:
        print("\nNo NCERT Exemplar chunks ingested. Check content/ncert_exemplar/.")

#!/usr/bin/env python3
"""Run the CBSE Class 10 Maths PYQ ingestion pipeline."""

import logging

from ingest.pyq_pipeline import run_pyq_ingestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


if __name__ == "__main__":
    count = run_pyq_ingestion()
    if count:
        print(f"\nIngested {count} PYQ question chunks into the PYQ FAISS corpus.")
    else:
        print("\nNo PYQ chunks ingested. Check content/math_cbse_pyqs/.")

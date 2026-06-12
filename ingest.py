#!/usr/bin/env python3
"""Run the NCERT PDF ingestion pipeline."""

import logging
import argparse

from config.settings import settings
from ingest.pipeline import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the NCERT textbook ingestion pipeline.")
    parser.add_argument("--subject", default="maths", choices=["maths", "science", "sst"])
    args = parser.parse_args()
    count = run_ingestion(subject=args.subject)
    if count:
        print(f"\nIngested {count} chunks from NCERT PDFs into FAISS.")
    else:
        print(f"\nNo chunks ingested. Check that PDFs exist in {settings.content_dir_for(args.subject, 'textbook')}/.")

#!/usr/bin/env python3
"""Run the CBSE Class 10 Maths PYQ ingestion pipeline."""

import logging
import argparse

from config.settings import settings
from ingest.pyq_pipeline import run_pyq_ingestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the CBSE Class 10 PYQ ingestion pipeline.")
    parser.add_argument("--subject", default="maths", choices=["maths", "science"])
    args = parser.parse_args()
    count = run_pyq_ingestion(subject=args.subject)
    if count:
        print(f"\nIngested {count} PYQ question chunks into the PYQ FAISS corpus.")
    else:
        print(f"\nNo PYQ chunks ingested. Check {settings.content_dir_for(args.subject, 'pyq')}/.")

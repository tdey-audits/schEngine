#!/usr/bin/env python3
"""Run the NCERT Exemplar ingestion pipeline."""

import logging
import argparse

from config.settings import settings
from ingest.exemplar_pipeline import run_exemplar_ingestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the NCERT Exemplar ingestion pipeline.")
    parser.add_argument("--subject", default="maths", choices=["maths", "science", "sst"])
    args = parser.parse_args()
    count = run_exemplar_ingestion(subject=args.subject)
    if count:
        print(f"\nIngested {count} NCERT Exemplar question chunks into the Exemplar FAISS corpus.")
    elif args.subject == "sst":
        print("\nNo SST Exemplar corpus is configured; skipped.")
    else:
        print(f"\nNo NCERT Exemplar chunks ingested. Check {settings.content_dir_for(args.subject, 'exemplar')}/.")

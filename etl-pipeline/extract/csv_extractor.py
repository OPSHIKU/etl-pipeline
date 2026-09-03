"""
csv_extractor.py
-----------------
Extract stage for the CSV data source. Reads the raw file as strings
only (no type coercion here) — type coercion and business rules belong
to the validation/schema layer, not extraction. This keeps Extract
"dumb" and auditable: it always ingests the file byte-for-byte.
"""

from pathlib import Path
from typing import List, Dict, Any
import csv


def extract_csv(path: Path, logger) -> List[Dict[str, Any]]:
    logger.info(f"Extracting CSV source: {path}")
    if not path.exists():
        logger.error(f"CSV source not found at {path}")
        raise FileNotFoundError(f"CSV source not found at {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = [row for row in reader]

    logger.info(f"Extracted {len(records)} raw rows from {path.name}")
    return records

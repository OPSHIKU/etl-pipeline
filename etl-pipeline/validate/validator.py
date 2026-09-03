"""
validator.py
------------
Runs a list of raw dict records through a given Pydantic schema.
Returns (valid_records, rejected_records) where each rejected record
carries the original data plus the specific validation errors — this is
what makes the validation "automated" and auditable rather than a
silent try/except that swallows bad data.
"""

from typing import Type, List, Tuple, Dict, Any
from pydantic import BaseModel, ValidationError


def validate_records(
    raw_records: List[Dict[str, Any]],
    schema: Type[BaseModel],
    logger,
    source_name: str,
) -> Tuple[List[BaseModel], List[Dict[str, Any]]]:
    valid: List[BaseModel] = []
    rejected: List[Dict[str, Any]] = []

    for i, record in enumerate(raw_records):
        try:
            validated = schema.model_validate(record)
            valid.append(validated)
        except ValidationError as e:
            rejected.append(
                {
                    "row_index": i,
                    "raw_record": record,
                    "errors": e.errors(include_url=False),
                }
            )
            logger.warning(
                f"[{source_name}] Row {i} REJECTED: "
                f"{[err['msg'] for err in e.errors()]} | raw={record}"
            )

    reject_rate = len(rejected) / len(raw_records) if raw_records else 0
    logger.info(
        f"[{source_name}] Validation complete: {len(valid)} passed, "
        f"{len(rejected)} rejected ({reject_rate:.1%} reject rate)."
    )
    return valid, rejected

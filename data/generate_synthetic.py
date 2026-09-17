"""Deterministic reference data, not a representation of production schemas."""

import argparse
import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


def records(columns, rows):
    return [dict(zip(columns.split(), row, strict=True)) for row in rows]


def build_inputs():
    return {
        "documents": records("document_id title owner business_status document_type", [
            ("D001", "Synthetic welcome kit", "Member Operations", "Active", "Member communication"),
            ("D002", "Synthetic explanation of benefits", "Claims", "Active", "Claims communication"),
            ("D003", "Synthetic enrollment guide", "Benefits", "Active", "Enrollment communication"),
            ("D004", "Synthetic provider notice", "Provider Communications", "Active", "Provider communication"),
            ("D005", "Synthetic retired form", "Records", "Archived", "Form"),
            ("D006", "Synthetic renewal packet", "", "Proposed", "Member communication"),
        ]),
        "revisions": records("revision_id document_id revision_number revision_status effective_date end_date publication_date channel", [
            ("R001", "D001", "1", "Retired", "2025-01-01", "2026-12-31", "2024-12-15", "Print"),
            ("R002", "D001", "2", "Published", "2027-01-01", "", "2026-12-15", "Print"),
            ("R003", "D002", "1", "Published", "2026-01-01", "", "2025-12-15", "Digital"),
            ("R004", "D003", "1", "Published", "2026-01-01", "", "2025-12-15", "Print"),
            ("R005", "D004", "1", "Published", "2026-01-01", "", "2025-12-15", "Digital"),
            ("R006", "D005", "1", "Archived", "2025-01-01", "2025-12-31", "2024-12-15", "Print"),
            ("R007", "D006", "1", "Draft", "2027-02-01", "", "", "Print"),
            ("R008", "D003", "2", "Draft", "2027-02-01", "", "", "Digital"),
        ]),
        "jobs": records("job_id revision_id vendor_id cost_center_id production_date quantity expected_cost", [
            ("J001", "R002", "V001", "CC001", "2026-12-16", "1000", "2000.00"),
            ("J002", "R003", "V002", "CC002", "2026-09-01", "5000", "250.00"),
            ("J003", "R004", "V001", "CC001", "2026-09-01", "2000", "3000.00"),
            ("J004", "R005", "V002", "CC003", "2026-09-01", "1000", "100.00"),
            ("J005", "R001", "V001", "CC001", "2025-06-01", "500", "1000.00"),
            ("J006", "R007", "V003", "CC001", "2027-01-10", "100", "300.00"),
            ("J007", "R004", "V003", "CC001", "2026-09-02", "1000", "1800.00"),
        ]),
        "vendors": records("vendor_id vendor_name", [
            ("V001", "Synthetic Print North"), ("V002", "Synthetic Digital Services"),
            ("V003", "Synthetic Print South"),
        ]),
        "cost_centers": records("cost_center_id cost_center_name", [
            ("CC001", "Member Communications"), ("CC002", "Claims"), ("CC003", "Provider Relations"),
        ]),
        "invoice_lines": records("source_line_id vendor_id invoice_id line_number job_id amount currency", [
            ("L001", "V001", "INV100", "1", "J001", "2100.00", "USD"),
            ("L002", "V001", "INV100", "2", "J003", "3200.00", "USD"),
            ("L003", "V002", "INV200", "1", "J002", "250.00", "USD"),
            ("L004", "V002", "INV200", "2", "J004", "125.00", "USD"),
            ("L005", "V001", "INV101", "1", "J005", "1000.00", "USD"),
            ("L006", "V003", "INV300", "1", "J007", "1800.00", "USD"),
            ("L007", "V001", "CREDIT100", "1", "J001", "-100.00", "USD"),
            ("L008", "V003", "INV301", "1", "J999", "400.00", "USD"),
            ("L009", "V001", "INV100", "1", "J001", "2100.00", "USD"),
            ("L010", "V002", "INV201", "1", "J002", "NOT-A-NUMBER", "USD"),
            ("L011", "V001", "INV102", "1", "J003", "50.00", "USD"),
            ("L012", "V003", "INV302", "1", "J006", "300.00", "USD"),
            ("L013", "V003", "INV303", "1", "J001", "80.00", "USD"),
        ]),
    }


def unique_index(rows, key):
    indexed = {row[key]: row for row in rows}
    if len(indexed) != len(rows) or "" in indexed:
        raise ValueError(f"Nonunique or empty key: {key}")
    return indexed


def reconcile(inputs):
    documents = unique_index(inputs["documents"], "document_id")
    revisions = unique_index(inputs["revisions"], "revision_id")
    jobs = unique_index(inputs["jobs"], "job_id")
    vendors = unique_index(inputs["vendors"], "vendor_id")
    centers = unique_index(inputs["cost_centers"], "cost_center_id")
    unique_index(inputs["invoice_lines"], "source_line_id")
    for revision in revisions.values():
        if revision["document_id"] not in documents:
            raise ValueError("Orphan revision")
    for job in jobs.values():
        if (job["revision_id"] not in revisions or job["vendor_id"] not in vendors
                or job["cost_center_id"] not in centers):
            raise ValueError("Orphan job reference")
    seen = set()
    dispositions = []
    for row in sorted(inputs["invoice_lines"], key=lambda value: value["source_line_id"]):
        key = (row["vendor_id"], row["invoice_id"], row["line_number"])
        try:
            amount = Decimal(row["amount"])
            if not amount.is_finite() or amount != amount.quantize(Decimal("0.01")):
                raise InvalidOperation
        except InvalidOperation:
            amount = None
        if key in seen:
            disposition, reason = "Rejected", "DUPLICATE_LINE"
        elif amount is None:
            disposition, reason = "Rejected", "INVALID_AMOUNT"
        elif row["currency"] != "USD":
            disposition, reason = "Rejected", "UNSUPPORTED_CURRENCY"
        elif row["job_id"] not in jobs:
            disposition, reason = "Unmatched", "UNKNOWN_JOB"
        elif jobs[row["job_id"]]["vendor_id"] != row["vendor_id"]:
            disposition, reason = "Unmatched", "VENDOR_MISMATCH"
        else:
            disposition, reason = "Matched", "OK"
        seen.add(key)
        dispositions.append({**row, "parsed_amount": amount,
                             "disposition": disposition, "reason": reason})
    totals = {
        bucket: sum((row["parsed_amount"] or Decimal(0) for row in dispositions
                     if row["disposition"] == bucket), Decimal(0))
        for bucket in ("Matched", "Unmatched", "Rejected")
    }
    job_costs = []
    for job in jobs.values():
        actual = sum((row["parsed_amount"] for row in dispositions
                      if row["disposition"] == "Matched" and row["job_id"] == job["job_id"]), Decimal(0))
        job_costs.append({**job, "actual_cost": actual,
                          "variance": actual - Decimal(job["expected_cost"])})
    return {"invoice_disposition": dispositions, "job_cost": job_costs, "totals": totals}


def generate(destination):
    destination.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    reference = reconcile(inputs)
    hashes = {}
    for name, rows in inputs.items():
        path = destination / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "synthetic_only": True, "schema_version": "1.0", "snapshot_id": "DOCUMENT-DEMO-001",
        "as_of_date": "2027-01-01", "currency": "USD",
        "row_counts": {name: len(rows) for name, rows in inputs.items()},
        "sha256": hashes, "expected": reference,
    }
    (destination / "expected.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "sample")
    arguments = parser.parse_args()
    result = generate(arguments.output)
    print(json.dumps({"rows": result["row_counts"], "totals": result["expected"]["totals"]}, default=str))
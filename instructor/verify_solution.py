"""Capture instructor SQL/model evidence; optional probes touch synthetic staging only."""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from instructor.fabric import FabricClient


DOCUMENT_MEASURES = {
    "Catalog Items": 6, "Current Publications": 4, "Missing Owners": 1,
    "Catalog Coverage": 4 / 6, "Revision Count": 8, "Job Count": 7,
    "Produced Units": 10600, "Matched Job Spend": 8725, "Expected Job Cost": 8450,
    "Cost Variance": 275, "Cost Per Produced Unit": 0.8231,
    "Illustrative 5 Percent Reduction": 436.25, "Source Parseable Amount": 11305,
    "Unmatched Amount": 480, "Rejected Parseable Amount": 2100, "Unparseable Lines": 1,
}
ENROLLMENT_MEASURES = {
    "Member Count": 13, "Subscribers": 7, "Dependents": 6, "Exception Count": 16,
    "Affected Members": 10, "Exception Member Rate": 10 / 13, "Source Members": 13,
    "Coverage Elections": 26, "Parser Issues": 0, "Member Reconciliation Difference": 0,
}


def assert_values(actual, expected):
    for name, value in expected.items():
        observed = actual.get(name, actual.get(f"[{name}]"))
        if observed is None or not math.isclose(float(observed), value, rel_tol=1e-8, abs_tol=1e-8):
            raise AssertionError(f"{name}: expected {value}, observed {observed}")


def model_values(client, bindings, expected):
    scope = "https://analysis.windows.net/powerbi/api/.default"
    token = client.credential.get_token(scope).token
    query = "EVALUATE ROW(" + ", ".join(f'"{name}", [{name}]' for name in expected) + ")"
    response = client.session.post(
        f"https://api.powerbi.com/v1.0/myorg/groups/{bindings['workspace']}/datasets/{bindings['semantic_model']}/executeQueries",
        headers={"Authorization": f"Bearer {token}"},
        json={"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}},
        timeout=(30, 180), allow_redirects=False,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Power BI model query HTTP {response.status_code}: {response.text[:1000]}")
    rows = response.json()["results"][0]["tables"][0]["rows"]
    if len(rows) != 1:
        raise AssertionError("Expected exactly one DAX result row")
    assert_values(rows[0], expected)
    return rows[0]


def verify(client, bindings, root=ROOT, replay=False, failure_probe=False):
    for name in ("workspace", "warehouse", "semantic_model", "pipeline"):
        UUID(bindings[name])
    if bindings.get("synthetic_only") is not True:
        raise ValueError("Explicit synthetic_only binding is required")
    enrollment = (root / "src" / "parse_834.py").exists()
    jobs = list(client.pages(f"/v1/workspaces/{bindings['workspace']}/items/{bindings['pipeline']}/jobs/instances"))
    if any(job["status"] in ("InProgress", "NotStarted") for job in jobs):
        raise RuntimeError("A pipeline is active; serialized verification must wait")
    workspace, warehouse = bindings["workspace"], bindings["warehouse"]

    def sql(text):
        return client.sql(workspace, warehouse, text)

    validation = (root / "sql" / "03_validate.sql").read_text(encoding="utf-8")

    def check():
        failures = sql(validation)
        if any(failures):
            raise AssertionError(f"Warehouse acceptance failed: {failures}")

    snapshot_query = (
        "SELECT * FROM dbo.report_members ORDER BY member_ordinal; "
        "SELECT * FROM dbo.report_exceptions ORDER BY member_ordinal,rule_code,benefit; SELECT * FROM dbo.report_health;"
        if enrollment else
        "SELECT * FROM dbo.report_catalog ORDER BY document_id; SELECT * FROM dbo.dim_revision ORDER BY revision_id; "
        "SELECT * FROM dbo.fact_job_cost ORDER BY job_id; SELECT * FROM dbo.invoice_disposition ORDER BY source_line_id; "
        "SELECT * FROM dbo.report_reconciliation ORDER BY disposition;"
    )
    publication = "EXEC dbo.publish_enrollment_products;" if enrollment else "EXEC dbo.publish_document_products;"
    check()
    before = sql(snapshot_query)
    result = {"sql_acceptance": "passed", "published_snapshot": before,
              "pipeline_jobs": jobs[:10], "replay": "not_requested", "failure_probe": "not_requested"}
    if replay:
        sql(publication)
        check()
        if sql(snapshot_query) != before:
            raise AssertionError("Publication replay changed the expected product snapshot")
        result["replay"] = "passed"
    if failure_probe:
        if enrollment:
            original = sql("SELECT attempt_id FROM dbo.stg_manifest;")[0][0]["attempt_id"]
            UUID(original)
            failed_attempt = str(uuid4())
            mutation = f"UPDATE dbo.stg_manifest SET attempt_id='{failed_attempt}', status='Failed', failure_code='INSTRUCTOR_SYNTHETIC_PROBE';"
            restore = f"UPDATE dbo.stg_manifest SET attempt_id='{original}', status='Succeeded', failure_code='';"
            expected_error = "Failed or empty parse cannot publish"
        else:
            original = sql("SELECT quantity FROM dbo.stg_jobs WHERE job_id='J001';")[0][0]["quantity"]
            if not str(original).isdigit():
                raise AssertionError("Expected the original positive synthetic J001 quantity")
            mutation = "UPDATE dbo.stg_jobs SET quantity='NOT-A-NUMBER' WHERE job_id='J001';"
            restore = f"UPDATE dbo.stg_jobs SET quantity='{original}' WHERE job_id='J001';"
            expected_error = "Invalid catalog/job references, dates, quantities or costs block publication"
        caught = None
        try:
            sql(mutation)
            try:
                sql(publication)
            except Exception as error:
                caught = str(error)
            if not caught or expected_error not in caught:
                raise AssertionError(f"Expected the specific publication guard, observed: {caught}")
            if sql(snapshot_query) != before:
                raise AssertionError("Failed publication changed the successful product snapshot")
        finally:
            sql(restore)
        check()
        audit_query = (f"SELECT * FROM dbo.audit_run WHERE attempt_id='{failed_attempt}';" if enrollment else
                       "SELECT TOP (3) * FROM dbo.publication_history ORDER BY published_at DESC;")
        result["failure_probe"] = {"status": "passed", "expected_guard": expected_error, "audit": sql(audit_query)}
    result["model_values"] = model_values(client, bindings, ENROLLMENT_MEASURES if enrollment else DOCUMENT_MEASURES)
    result["report_rendering"] = "not_checked_by_this_command"
    result["non_owner_access"] = "unverified"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "evidence" / "acceptance.json")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--failure-probe", action="store_true")
    arguments = parser.parse_args()
    bindings = json.loads(arguments.bindings.read_text(encoding="utf-8"))
    evidence = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "workspace": bindings["workspace"]}
    try:
        evidence.update(verify(FabricClient(), bindings, replay=arguments.replay, failure_probe=arguments.failure_probe), status="passed")
    except Exception as error:
        evidence.update(status="failed", error=str(error))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(evidence, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({name: value for name, value in evidence.items() if name != "published_snapshot"}, indent=2, default=str))
    sys.exit(0 if evidence["status"] == "passed" else 1)
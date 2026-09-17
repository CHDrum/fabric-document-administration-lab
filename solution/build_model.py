"""Create an explicitly bound Direct Lake model over physical Warehouse products."""

import argparse
import base64
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


TABLES = {
    "Catalog": ("report_catalog", {
        "document_id": "string", "title": "string", "owner": "string", "business_status": "string",
        "document_type": "string", "current_revision_id": "string", "revision_number": "int64",
        "channel": "string", "publication_date": "dateTime", "effective_date": "dateTime",
        "has_current_publication": "int64", "missing_owner": "int64", "as_of_date": "dateTime"}),
    "Revision": ("dim_revision", {
        "revision_id": "string", "document_id": "string", "revision_number": "int64",
        "revision_status": "string", "effective_date": "dateTime", "end_date": "dateTime",
        "publication_date": "dateTime", "channel": "string"}),
    "Jobs": ("fact_job_cost", {
        "job_id": "string", "revision_id": "string", "document_id": "string", "vendor_id": "string",
        "cost_center_id": "string", "production_date": "dateTime", "channel": "string",
        "quantity": "int64", "expected_cost": "decimal", "actual_cost": "decimal", "variance": "decimal"}),
    "Vendor": ("dim_vendor", {"vendor_id": "string", "vendor_name": "string"}),
    "CostCenter": ("dim_cost_center", {"cost_center_id": "string", "cost_center_name": "string"}),
    "Reconciliation": ("report_reconciliation", {
        "disposition": "string", "line_count": "int64", "parseable_amount": "decimal", "unparseable_count": "int64"}),
    "InvoiceReview": ("invoice_disposition", {
        "source_line_id": "string", "vendor_id": "string", "invoice_id": "string", "line_number": "string",
        "job_id": "string", "raw_amount": "string", "parsed_amount": "decimal", "currency": "string",
        "disposition": "string", "reason": "string"}),
}

MEASURES = {
    "Catalog": [("Catalog Items", "COUNTROWS('Catalog')", "#,0"),
        ("Current Publications", "SUM('Catalog'[has_current_publication])", "#,0"),
        ("Missing Owners", "SUM('Catalog'[missing_owner])", "#,0"),
        ("Catalog Coverage", "DIVIDE([Current Publications], [Catalog Items])", "0.0%")],
    "Revision": [("Revision Count", "COUNTROWS('Revision')", "#,0")],
    "Jobs": [("Job Count", "COUNTROWS('Jobs')", "#,0"),
        ("Produced Units", "SUM('Jobs'[quantity])", "#,0"),
        ("Matched Job Spend", "SUM('Jobs'[actual_cost])", "$#,0.00;($#,0.00)"),
        ("Expected Job Cost", "SUM('Jobs'[expected_cost])", "$#,0.00;($#,0.00)"),
        ("Cost Variance", "SUM('Jobs'[variance])", "$#,0.00;($#,0.00)"),
        ("Cost Per Produced Unit", "DIVIDE([Matched Job Spend], [Produced Units])", "$0.0000"),
        ("Illustrative 5 Percent Reduction", "[Matched Job Spend] * 0.05", "$#,0.00")],
    "Reconciliation": [("Source Parseable Amount", "SUM('Reconciliation'[parseable_amount])", "$#,0.00"),
        ("Unmatched Amount", "CALCULATE(SUM('Reconciliation'[parseable_amount]), 'Reconciliation'[disposition] = \"Unmatched\")", "$#,0.00"),
        ("Rejected Parseable Amount", "CALCULATE(SUM('Reconciliation'[parseable_amount]), 'Reconciliation'[disposition] = \"Rejected\")", "$#,0.00"),
        ("Unparseable Lines", "SUM('Reconciliation'[unparseable_count])", "#,0")],
}


def build(endpoint, database="DocumentProducts"):
    if not endpoint.endswith(".datawarehouse.fabric.microsoft.com") or any(character in endpoint for character in '\";\r\n'):
        raise ValueError("Use the Warehouse SQL endpoint host, without credentials")
    expression = f'Sql.Database({json.dumps(endpoint)}, {json.dumps(database)}, [CreateNavigationProperties=false])'
    tables = []
    for name, (source, fields) in TABLES.items():
        columns = [{"name": field, "sourceColumn": field, "dataType": kind, "summarizeBy": "none",
                    "lineageTag": str(uuid5(NAMESPACE_URL, f"fabric/document/{name}/{field}")),
                    **({"formatString": "yyyy-MM-dd"} if kind == "dateTime" else {})}
                   for field, kind in fields.items()]
        tables.append({"name": name, "columns": columns,
            "lineageTag": str(uuid5(NAMESPACE_URL, f"fabric/document/{name}")),
            "partitions": [{"name": name, "mode": "directLake", "source": {
                "type": "entity", "entityName": source, "schemaName": "dbo", "expressionSource": "Warehouse"}}],
            "measures": [{"name": measure, "expression": dax, "formatString": formatting,
                "description": "Synthetic teaching data only. Scenario reductions are not achieved savings."}
                for measure, dax, formatting in MEASURES.get(name, [])]})
    relationships = [{"name": f"{source}_{target}_{key}", "fromTable": source, "fromColumn": key,
                      "toTable": target, "toColumn": key, "fromCardinality": "many", "toCardinality": "one",
                      "crossFilteringBehavior": "oneDirection"}
                     for source, target, key in [("Jobs", "Catalog", "document_id"),
                        ("Revision", "Catalog", "document_id"), ("Jobs", "Vendor", "vendor_id"),
                        ("Jobs", "CostCenter", "cost_center_id")]]
    return {"compatibilityLevel": 1604, "model": {"culture": "en-US", "sourceQueryCulture": "en-US",
        "defaultPowerBIDataSourceVersion": "powerBI_V3", "discourageImplicitMeasures": True,
        "expressions": [{"name": "Warehouse", "kind": "m", "expression": expression}],
        "tables": tables, "relationships": relationships}}


def item_payload(model):
    properties = {"version": "4.0", "settings": {"qnaEnabled": False}}
    return {"displayName": "DocumentAnalytics", "type": "SemanticModel",
        "description": "Synthetic catalog, job-grain spend and reconciliation. No achieved-savings claim.",
        "definition": {"format": "TMSL", "parts": [
            {"path": name, "payloadType": "InlineBase64", "payload": base64.b64encode(json.dumps(value).encode()).decode()}
            for name, value in [("model.bim", model), ("definition.pbism", properties)]]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--database", default="DocumentProducts")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(item_payload(build(arguments.endpoint, arguments.database)), indent=2), encoding="utf-8")
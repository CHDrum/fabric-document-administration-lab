"""Build the original three-page Fabric teaching report in the public PBIR format."""

import argparse
import base64
import json
from pathlib import Path
from uuid import UUID


SCHEMA_ROOT = "https://developer.microsoft.com/json-schemas/fabric/item/report"


def expression(value):
    literal = "true" if value is True else "false" if value is False else str(value) if isinstance(value, (int, float)) else "'" + value.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": literal}}}


def field(table, name, measure=False):
    return {"Measure" if measure else "Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def projection(table, name, measure=False):
    return {"field": field(table, name, measure), "queryRef": f"{table}.{name}", "nativeQueryRef": name}


def visual(name, kind, title, position, roles):
    left, top, width, height = position
    return {"$schema": f"{SCHEMA_ROOT}/definition/visualContainer/2.0.0/schema.json", "name": name,
        "position": {"x": left, "y": top, "width": width, "height": height, "z": top * 10 + left, "tabOrder": top * 10 + left},
        "visual": {"visualType": kind, "query": {"queryState": {
            role: {"projections": values} for role, values in roles.items()}},
            "visualContainerObjects": {"title": [{"properties": {"show": expression(True), "text": expression(title), "fontSize": expression(12)}}],
                "background": [{"properties": {"color": {"solid": {"color": expression("#FFFFFF")}}, "transparency": expression(0)}}]},
            "drillFilterOtherVisuals": True}}


def heading(name, title, subtitle):
    content = visual(name, "textbox", title, (24, 12, 1232, 74), {})
    content["visual"].pop("query")
    content["visual"]["visualContainerObjects"]["title"][0]["properties"]["show"] = expression(False)
    content["visual"]["objects"] = {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": title, "textStyle": {"fontSize": "22pt", "fontWeight": "bold", "color": "#005B85"}}]},
        {"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "10pt", "color": "#455560"}}]}]}}]}
    return content


def table(name, title, position, fields):
    return visual(name, "tableEx", title, position, {"Values": [projection(*entry) for entry in fields]})


def cards(measures):
    result = []
    for ordinal, (source, measure, label) in enumerate(measures):
        content = visual(f"metric{ordinal}", "card", label, (24 + ordinal * 310, 90, 296, 110),
                         {"Values": [projection(source, measure, True)]})
        content["visual"]["objects"] = {
            "categoryLabels": [{"properties": {"show": expression(False)}}],
            "labels": [{"properties": {"fontSize": expression(32), "labelDisplayUnits": expression(1)}}]}
        result.append(content)
    return result


def pages():
    return [
        ("catalog", "01 Catalog and Lifecycle", [
            heading("heading", "Document Catalog", "SYNTHETIC WORKSHOP  |  As of 2027-01-01  |  Items and revisions have different grains"),
            *cards([("Catalog", "Catalog Items", "Catalog items"), ("Catalog", "Current Publications", "Current publications"),
                    ("Catalog", "Missing Owners", "Missing owners"), ("Revision", "Revision Count", "Historical revisions")]),
            table("catalogRows", "Ownership and current publication", (24, 218, 1232, 220),
                [("Catalog", name) for name in ("document_id", "title", "owner", "business_status", "current_revision_id", "channel")]),
            table("revisionRows", "Revision history, including retired and future drafts", (24, 454, 1232, 242),
                [("Revision", name) for name in ("document_id", "revision_id", "revision_number", "revision_status", "effective_date", "publication_date", "channel")])]),
        ("spend", "02 Spend and Cost Drivers", [
            heading("heading", "Spend and Cost Drivers", "SYNTHETIC USD  |  Job grain  |  Invoice credits and extra lines are netted before the job join"),
            *cards([("Jobs", "Matched Job Spend", "Matched job spend"), ("Jobs", "Expected Job Cost", "Expected job cost"),
                    ("Jobs", "Cost Variance", "Cost variance"), ("Jobs", "Cost Per Produced Unit", "Cost per produced unit")]),
            visual("vendorSpend", "barChart", "Spend by vendor", (24, 218, 604, 260),
                {"Category": [projection("Vendor", "vendor_name")], "Y": [projection("Jobs", "Matched Job Spend", True)]}),
            visual("channelSpend", "barChart", "Spend by job channel", (652, 218, 604, 260),
                {"Category": [projection("Jobs", "channel")], "Y": [projection("Jobs", "Matched Job Spend", True)]}),
            table("jobRows", "One row per production job", (24, 494, 1232, 202),
                [("Jobs", name) for name in ("job_id", "document_id", "channel", "quantity", "expected_cost", "actual_cost", "variance")])]),
        ("reconciliation", "03 Reconciliation and Scenario", [
            heading("heading", "Reconciliation", "SYNTHETIC USD  |  Scenario is illustrative, not a forecast or achieved savings"),
            *cards([("Reconciliation", "Source Parseable Amount", "Source parseable amount"), ("Reconciliation", "Unmatched Amount", "Unmatched amount"),
                    ("Reconciliation", "Rejected Parseable Amount", "Rejected parseable amount"), ("Jobs", "Illustrative 5 Percent Reduction", "Illustrative 5% matched-spend reduction")]),
            table("reconciliationRows", "Parseable source = matched + unmatched + rejected; invalid amounts remain counted", (24, 218, 1232, 160),
                [("Reconciliation", name) for name in ("disposition", "line_count", "parseable_amount", "unparseable_count")]),
            table("invoiceRows", "Line-level review, including unmatched and rejected lines", (24, 394, 1232, 302),
                [("InvoiceReview", name) for name in ("source_line_id", "job_id", "raw_amount", "parsed_amount", "disposition", "reason")])]),
    ]


def build(semantic_model, page_definitions=None):
    UUID(semantic_model)
    page_definitions = pages() if page_definitions is None else page_definitions
    theme = {"name": "FabricWorkshop", "dataColors": ["#007CB2", "#00877D", "#F0B323", "#D8493C", "#718642", "#785E9D"],
             "background": "#FFFFFF", "foreground": "#203B47", "tableAccent": "#007CB2"}
    parts = {
        "definition.pbir": {"$schema": f"{SCHEMA_ROOT}/definitionProperties/2.0.0/schema.json", "version": "4.0",
            "datasetReference": {"byConnection": {"connectionString": f"semanticmodelid={semantic_model}"}}},
        "definition/version.json": {"$schema": f"{SCHEMA_ROOT}/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"},
        "definition/report.json": {"$schema": f"{SCHEMA_ROOT}/definition/report/2.0.0/schema.json",
            "themeCollection": {"baseTheme": {"name": "CY24SU06", "type": "SharedResources", "reportVersionAtImport": "5.55"},
                "customTheme": {"name": "FabricWorkshop", "type": "RegisteredResources", "reportVersionAtImport": "5.55"}},
            "resourcePackages": [{"name": "SharedResources", "type": "SharedResources", "items": [
                {"name": "CY24SU06", "path": "BaseThemes/CY24SU06.json", "type": "BaseTheme"}]},
                {"name": "RegisteredResources", "type": "RegisteredResources", "items": [
                {"name": "FabricWorkshop", "path": "FabricWorkshop.json", "type": "CustomTheme"}]}],
            "settings": {"useEnhancedTooltips": True, "defaultFilterActionIsDataFilter": True}},
        "StaticResources/RegisteredResources/FabricWorkshop.json": theme,
        "definition/pages/pages.json": {"$schema": f"{SCHEMA_ROOT}/definition/pagesMetadata/1.0.0/schema.json",
            "pageOrder": [name for name, _, _ in page_definitions], "activePageName": page_definitions[0][0]},
    }
    for name, label, visuals in page_definitions:
        parts[f"definition/pages/{name}/page.json"] = {"$schema": f"{SCHEMA_ROOT}/definition/page/2.0.0/schema.json",
            "name": name, "displayName": label, "displayOption": "FitToPage", "height": 720, "width": 1280}
        for content in visuals:
            parts[f"definition/pages/{name}/visuals/{content['name']}/visual.json"] = content
    return parts


def item_payload(parts):
    return {"displayName": "Fabric Document Administration", "type": "Report",
        "description": "Synthetic catalog, job-level spend, financial reconciliation and illustrative scenario.",
        "definition": {"format": "PBIR", "parts": [{"path": path, "payloadType": "InlineBase64",
            "payload": base64.b64encode(json.dumps(content).encode()).decode()} for path, content in parts.items()]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(item_payload(build(arguments.model)), indent=2), encoding="utf-8")
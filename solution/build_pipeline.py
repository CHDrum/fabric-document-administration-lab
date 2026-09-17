"""Build a portable Fabric pipeline definition from explicit target bindings."""

import argparse
import base64
import json
from pathlib import Path


TABLES = ("documents", "revisions", "jobs", "vendors", "cost_centers", "invoice_lines")


def linked_service(kind, workspace, item, endpoint=None):
    properties = {"workspaceId": workspace, "artifactId": item}
    if endpoint:
        properties["endpoint"] = endpoint
    if kind == "Lakehouse":
        properties["rootFolder"] = "Files"
    return {"name": kind, "properties": {"type": kind, "typeProperties": properties, "annotations": []}}


def copy_activity(table, workspace, lakehouse, warehouse, endpoint, predecessor=None):
    if table not in TABLES:
        raise ValueError("Unknown synthetic source table")
    source = {
        "type": "DelimitedTextSource",
        "storeSettings": {"type": "LakehouseReadSettings", "recursive": False, "enablePartitionDiscovery": False},
        "formatSettings": {"type": "DelimitedTextReadSettings"},
        "datasetSettings": {
            "annotations": [], "type": "DelimitedText",
            "schema": [],
            "linkedService": linked_service("Lakehouse", workspace, lakehouse),
            "typeProperties": {
                "location": {"type": "LakehouseLocation", "fileName": f"{table}.csv",
                             "folderPath": "document-demo/DOCUMENT-DEMO-001"},
                "columnDelimiter": ",", "rowDelimiter": "\n", "encodingName": "UTF-8",
                "escapeChar": "\\", "firstRowAsHeader": True, "quoteChar": '"',
            },
        },
    }
    sink = {
        "type": "DataWarehouseSink", "allowCopyCommand": True, "copyCommandSettings": {},
        "preCopyScript": f"DELETE FROM dbo.stg_{table};",
        "datasetSettings": {
            "annotations": [], "type": "DataWarehouseTable", "schema": [],
            "linkedService": linked_service("DataWarehouse", workspace, warehouse, endpoint),
            "typeProperties": {"schema": "dbo", "table": f"stg_{table}"},
        },
    }
    return {
        "name": f"Copy_{table}", "type": "Copy",
        "dependsOn": [{"activity": predecessor, "dependencyConditions": ["Succeeded"]}] if predecessor else [],
        "policy": {"timeout": "0.01:00:00", "retry": 1, "retryIntervalInSeconds": 30,
                   "secureOutput": False, "secureInput": False},
        "typeProperties": {
            "source": source, "sink": sink, "enableStaging": True,
            "translator": {"type": "TabularTranslator", "typeConversion": True,
                           "typeConversionSettings": {"allowDataTruncation": False, "treatBooleanAsNumber": False}},
        },
    }


def build(workspace, lakehouse, warehouse, endpoint, probe=False):
    activities = []
    for table in TABLES[:1] if probe else TABLES:
        activities.append(copy_activity(table, workspace, lakehouse, warehouse, endpoint,
                                        activities[-1]["name"] if activities else None))
    if not probe:
        activities.append({
            "name": "Publish_products", "type": "Script",
            "dependsOn": [{"activity": activities[-1]["name"], "dependencyConditions": ["Succeeded"]}],
            "linkedService": linked_service("DataWarehouse", workspace, warehouse, endpoint),
            "typeProperties": {"scripts": [{"type": "NonQuery", "text": "EXEC dbo.publish_document_products;"}],
                               "scriptBlockExecutionTimeout": "00:30:00"},
        })
    return {"properties": {"activities": activities}}


def item_payload(content, name="DocumentIngestion"):
    return {"displayName": name, "type": "DataPipeline", "description": "Synthetic reference data load and atomic publication.",
            "definition": {"parts": [{"path": "pipeline-content.json", "payloadType": "InlineBase64",
                                      "payload": base64.b64encode(json.dumps(content).encode()).decode()}]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--lakehouse", required=True)
    parser.add_argument("--warehouse", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("output/pipeline-request.json"))
    arguments = parser.parse_args()
    content = build(arguments.workspace, arguments.lakehouse, arguments.warehouse, arguments.endpoint, arguments.probe)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(item_payload(content), indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(content['properties']['activities'])} activities: {arguments.output}")
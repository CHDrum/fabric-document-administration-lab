"""Capture live instructor bindings and read-only item definitions without redeployment."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from instructor.fabric import FabricClient
from instructor.package_solution import write_package


def capture(client, workspace):
    UUID(workspace)
    manifest = json.loads((ROOT / "solution" / "manifest.json").read_text(encoding="utf-8"))
    items = list(client.pages(f"/v1/workspaces/{workspace}/items"))
    expected = {"lakehouse": (manifest["foundation_items"][0]["displayName"], "Lakehouse"),
        "warehouse": (manifest["foundation_items"][1]["displayName"], "Warehouse"),
        "pipeline": (manifest["pipeline_name"], "DataPipeline"),
        "semantic_model": (manifest["semantic_model_name"], "SemanticModel"),
        "report": (manifest["report_name"], "Report")}
    if "notebook_name" in manifest:
        expected.update(notebook=(manifest["notebook_name"], "Notebook"), environment=("EnrollmentRuntime", "Environment"))
    bindings = {"synthetic_only": True, "workspace": workspace}
    for key, (name, kind) in expected.items():
        matches = [item for item in items if item["displayName"] == name and item["type"] == kind]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {kind} named {name}")
        bindings[key] = matches[0]["id"]
    warehouse = client.request("GET", f"/v1/workspaces/{workspace}/warehouses/{bindings['warehouse']}")
    bindings.update(endpoint=warehouse["properties"]["connectionString"], database=warehouse["displayName"])
    location = ROOT / "solution" / "deployed"
    write_package(bindings, location)
    (ROOT / "instructor" / "bindings.local.json").write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")
    exports = {}
    for name in ("pipeline", "semantic_model", "report", "notebook"):
        if name not in bindings:
            continue
        response = client.request("POST", f"/v1/workspaces/{workspace}/items/{bindings[name]}/getDefinition")
        (location / f"export-{name}.json").write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
        exports[name] = response if response.get("status") == "Accepted" else {"status": "captured"}
    result = {"observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace": client.request("GET", f"/v1/workspaces/{workspace}"),
        "items": items, "definition_exports": exports,
        "note": "Requests are rebuilt from tested source; export files are service responses. Accepted exports need operation-result retrieval. No item or data was redeployed."}
    evidence = ROOT / "docs" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "inventory.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return {"bindings": bindings, "definition_exports": exports}


def resolve_exports(client, root=ROOT):
    location = root / "solution" / "deployed"
    inventory_path = root / "docs" / "evidence" / "inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    for path in sorted(location.glob("export-*.json")):
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if receipt.get("status") != "Accepted":
            continue
        operation = receipt["operationId"]
        UUID(operation)
        observed = client.request("GET", f"/v1/operations/{operation}")
        name = path.stem.removeprefix("export-")
        if observed.get("status") != "Succeeded":
            inventory["definition_exports"][name] = {"status": observed.get("status"), "operationId": operation}
            continue
        definition = client.request("GET", f"/v1/operations/{operation}/result")
        parts = definition.get("definition", {}).get("parts")
        if not parts:
            raise ValueError(f"No definition parts returned for {name}")
        path.write_text(json.dumps(definition, indent=2) + "\n", encoding="utf-8")
        inventory["definition_exports"][name] = {"status": "captured", "part_count": len(parts), "operationId": operation}
    inventory["exports_checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    return inventory["definition_exports"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--workspace")
    mode.add_argument("--resolve", action="store_true")
    arguments = parser.parse_args()
    client = FabricClient()
    result = resolve_exports(client) if arguments.resolve else capture(client, arguments.workspace)
    print(json.dumps(result, indent=2))
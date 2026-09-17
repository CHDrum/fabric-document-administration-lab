"""Start one explicitly named synthetic pipeline run after an idle preflight; never poll."""

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from instructor.fabric import FabricClient


def start(client, bindings, source_file=None):
    for name in ("workspace", "pipeline"):
        UUID(bindings[name])
    if bindings.get("synthetic_only") is not True:
        raise ValueError("Explicit synthetic-only binding is required")
    enrollment = (ROOT / "src" / "parse_834.py").exists()
    if enrollment and source_file not in ("synthetic_834.edi", "synthetic_100000.edi", "synthetic_200000.edi"):
        raise ValueError("Choose an approved synthetic source file")
    if not enrollment and source_file:
        raise ValueError("The document pipeline uses its frozen six-file snapshot")
    path = f"/v1/workspaces/{bindings['workspace']}/items/{bindings['pipeline']}/jobs/instances"
    if any(job["status"] in ("InProgress", "NotStarted") for job in client.pages(path)):
        raise RuntimeError("An existing pipeline run is active; no new run submitted")
    workspace = client.request("GET", f"/v1/workspaces/{bindings['workspace']}")
    capacity = next((item for item in client.pages("/v1/capacities") if item["id"] == workspace.get("capacityId")), None)
    if not capacity or capacity["state"] != "Active":
        raise RuntimeError("The assigned capacity is not accessible and Active; no run submitted or capacity changed")
    parameters = {"source_file": source_file} if enrollment else {}
    return client.request("POST", path + "?jobType=Pipeline", {"executionData": {"parameters": parameters}})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--source-file")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = start(FabricClient(), json.loads(arguments.bindings.read_text(encoding="utf-8")), arguments.source_file)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
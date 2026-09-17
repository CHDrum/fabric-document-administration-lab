"""Generate explicit, rebindable Fabric item requests without calling the service."""

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from solution import build_model, build_pipeline, build_report


def package(bindings):
    enrollment = (ROOT / "src" / "parse_834.py").exists()
    identifiers = ["workspace", "lakehouse", "warehouse", "semantic_model"]
    if enrollment:
        identifiers.append("notebook")
    for name in identifiers:
        if not bindings.get(name):
            raise ValueError(f"Missing binding: {name}")
        UUID(bindings[name])
    arguments = [bindings[name] for name in ("workspace", "lakehouse", "warehouse", "endpoint")]
    if enrollment:
        arguments.append(bindings["notebook"])
    model = build_model.build(bindings["endpoint"], bindings.get(
        "database", "EnrollmentProducts" if enrollment else "DocumentProducts"))
    requests = {
        "pipeline": build_pipeline.item_payload(build_pipeline.build(*arguments)),
        "semantic-model": build_model.item_payload(model),
        "report": build_report.item_payload(build_report.build(bindings["semantic_model"])),
    }
    reference = ["# Semantic Model Reference", "",
        "Generated from the same definition used for deployment. All data is synthetic.", "",
        "Create an explicit Direct Lake model over these physical Warehouse tables; do not select the views.", ""]
    for table in model["model"]["tables"]:
        source = table["partitions"][0]["source"]["entityName"]
        reference.extend([f"## {table['name']} (dbo.{source})", "",
            "Columns: " + ", ".join(f"`{column['name']}`" for column in table["columns"]), ""])
        for measure in table.get("measures", []):
            reference.extend([f"### {measure['name']}", "", "```dax",
                f"{measure['name']} = {measure['expression']}", "```",
                f"Format: `{measure['formatString']}`", ""])
    reference.extend(["## Relationships", "", "Use single-direction filtering from the one side to the many side.", ""])
    for relationship in model["model"]["relationships"]:
        reference.append(f"- `{relationship['toTable']}.{relationship['toColumn']}` (one) to "
            f"`{relationship['fromTable']}.{relationship['fromColumn']}` (many)")
    return requests, "\n".join(reference) + "\n"


def write_package(bindings, output):
    requests, reference = package(bindings)
    output.mkdir(parents=True, exist_ok=True)
    for name, request in requests.items():
        (output / f"{name}.request.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    (output / "measures.md").write_text(reference, encoding="utf-8")
    return requests


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, default=ROOT / "instructor" / "bindings.example.json")
    parser.add_argument("--output", type=Path, default=ROOT / "solution" / "portable")
    arguments = parser.parse_args()
    write_package(json.loads(arguments.bindings.read_text(encoding="utf-8")), arguments.output)
    print(f"Wrote three item requests and measures.md to {arguments.output}")
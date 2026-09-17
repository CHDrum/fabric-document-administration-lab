import base64
import json
from pathlib import Path

import pytest

from instructor.package_solution import package, write_package


def test_portable_package_decodes_and_writes_measures(tmp_path):
    root = Path(__file__).resolve().parents[1]
    bindings = json.loads((root / "instructor" / "bindings.example.json").read_text())
    requests = write_package(bindings, tmp_path)
    assert {request["type"] for request in requests.values()} == {"DataPipeline", "SemanticModel", "Report"}
    for name, request in requests.items():
        assert json.loads((tmp_path / f"{name}.request.json").read_text()) == request
        for part in request["definition"]["parts"]:
            assert json.loads(base64.b64decode(part["payload"]))
    reference = (tmp_path / "measures.md").read_text()
    assert "```dax" in reference
    assert "Relationships" in reference
    assert bindings["semantic_model"] in str(base64.b64decode(
        next(part for part in requests["report"]["definition"]["parts"] if part["path"] == "definition.pbir")["payload"]))
    with pytest.raises(ValueError, match="Missing binding"):
        package({})
    with pytest.raises(ValueError):
        package({**bindings, "workspace": "not-a-workspace"})


def test_rebinding_removes_all_previous_target_identifiers():
    from uuid import uuid4

    root = Path(__file__).resolve().parents[1]
    previous = json.loads((root / "instructor" / "bindings.example.json").read_text())
    target = {name: str(uuid4()) if name in ("workspace", "lakehouse", "warehouse", "notebook", "environment", "semantic_model")
              else value for name, value in previous.items()}
    target.update(endpoint="second-target.datawarehouse.fabric.microsoft.com", database="SecondProducts")
    requests, _ = package(target)
    definitions = "\n".join(base64.b64decode(part["payload"]).decode("utf-8")
        for request in requests.values() for part in request["definition"]["parts"])
    for name in ("workspace", "lakehouse", "warehouse", "notebook", "semantic_model", "endpoint"):
        if name in previous:
            assert previous[name] not in definitions
            assert target[name] in definitions
    assert "SecondProducts" in definitions


def test_distributed_definitions_are_portable_and_decodable():
    root = Path(__file__).resolve().parents[1]
    bindings = json.loads((root / "instructor" / "bindings.example.json").read_text(encoding="utf-8"))
    expected, _ = package(bindings)
    for name, request in expected.items():
        distributed = json.loads((root / "solution" / "portable" / f"{name}.request.json").read_text(encoding="utf-8"))
        assert distributed == request
        parts = distributed["definition"]["parts"]
        assert parts and len({part["path"] for part in parts}) == len(parts)
        for part in parts:
            assert part["payloadType"] == "InlineBase64"
            content = base64.b64decode(part["payload"], validate=True).decode("utf-8-sig")
            assert content.strip()
            if part["path"].endswith((".json", ".bim", ".pbir", ".ipynb")):
                json.loads(content)
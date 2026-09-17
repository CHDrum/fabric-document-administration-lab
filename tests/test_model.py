import base64
import json

import pytest

from solution.build_model import build, item_payload


def test_direct_lake_uses_physical_products_and_explicit_job_measures():
    model = build("sample.datawarehouse.fabric.microsoft.com")["model"]
    tables = {table["name"]: table for table in model["tables"]}
    assert len(tables) == 7
    for table in tables.values():
        partition = table["partitions"][0]
        assert partition["mode"] == "directLake"
        assert not partition["source"]["entityName"].startswith("v_")
    assert all(relationship["crossFilteringBehavior"] == "oneDirection" for relationship in model["relationships"])
    assert not any(relationship["fromTable"] == "InvoiceReview" for relationship in model["relationships"])
    spend = next(measure for measure in tables["Jobs"]["measures"] if measure["name"] == "Matched Job Spend")
    assert spend["expression"] == "SUM('Jobs'[actual_cost])"


def test_model_definition_rebinds_without_embedded_credentials():
    payload = item_payload(build("other.datawarehouse.fabric.microsoft.com", "ReboundWarehouse"))
    decoded = json.loads(base64.b64decode(payload["definition"]["parts"][0]["payload"]))
    assert "ReboundWarehouse" in decoded["model"]["expressions"][0]["expression"]
    assert payload["definition"]["format"] == "TMSL"
    with pytest.raises(ValueError):
        build("untrusted.example.com")
import base64
import json

from solution.build_pipeline import TABLES, build, item_payload


def test_independent_bindings_and_atomic_publish_dependency():
    content = build("workspace", "lakehouse", "warehouse", "sql-endpoint")
    activities = content["properties"]["activities"]
    assert len(activities) == 7
    for index, table in enumerate(TABLES):
        activity = activities[index]
        assert activity["name"] == f"Copy_{table}"
        assert activity["typeProperties"]["sink"]["preCopyScript"] == f"DELETE FROM dbo.stg_{table};"
        assert activity["typeProperties"]["enableStaging"] is True
        assert "stagingSettings" not in activity["typeProperties"]
        assert activity["typeProperties"]["source"]["datasetSettings"]["schema"] == []
        if index:
            assert activity["dependsOn"] == [{"activity": activities[index - 1]["name"], "dependencyConditions": ["Succeeded"]}]
    assert activities[-1]["dependsOn"][0]["activity"] == "Copy_invoice_lines"
    decoded = json.loads(base64.b64decode(item_payload(content)["definition"]["parts"][0]["payload"]))
    assert decoded == content
    assert "creationPayload" not in item_payload(content)


def test_probe_never_publishes_partial_source():
    activities = build("workspace", "lakehouse", "warehouse", "endpoint", probe=True)["properties"]["activities"]
    assert [activity["name"] for activity in activities] == ["Copy_documents"]
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from instructor.verify_solution import assert_values, model_values, verify


def test_measure_values_require_real_zero_and_exact_numbers():
    assert_values({"[Total]": 0, "Rate": 2 / 3}, {"Total": 0, "Rate": 2 / 3})
    for invalid in ({}, {"Total": None}, {"Total": 1}, {"Total": float("nan")}):
        with pytest.raises(AssertionError):
            assert_values(invalid, {"Total": 0})


def test_model_query_uses_one_bounded_row_and_no_redirects():
    response = Mock(status_code=200)
    response.json.return_value = {"results": [{"tables": [{"rows": [{"[Total]": 13}]}]}]}
    client = SimpleNamespace(credential=Mock(), session=Mock())
    client.credential.get_token.return_value.token = "test-token"
    client.session.post.return_value = response
    result = model_values(client, {"workspace": "workspace", "semantic_model": "model"}, {"Total": 13})
    assert result == {"[Total]": 13}
    kwargs = client.session.post.call_args.kwargs
    assert kwargs["json"]["queries"] == [{"query": 'EVALUATE ROW("Total", [Total])'}]
    assert kwargs["allow_redirects"] is False


def test_active_pipeline_blocks_staging_probes():
    bindings = {name: "00000000-0000-4000-8000-000000000001" for name in ("workspace", "warehouse", "semantic_model", "pipeline")}
    client = SimpleNamespace(pages=Mock(return_value=[{"status": "InProgress"}]), sql=Mock())
    with pytest.raises(ValueError, match="synthetic_only"):
        verify(client, bindings, failure_probe=True)
    bindings["synthetic_only"] = True
    with pytest.raises(RuntimeError, match="active"):
        verify(client, bindings, failure_probe=True)
    client.sql.assert_not_called()


def test_pipeline_start_blocks_inactive_capacity_without_mutation():
    from instructor.run_pipeline import ROOT, start

    bindings = {"synthetic_only": True, "workspace": "00000000-0000-4000-8000-000000000001",
                "pipeline": "00000000-0000-4000-8000-000000000002"}
    source = "synthetic_834.edi" if (ROOT / "src" / "parse_834.py").exists() else None
    client = SimpleNamespace(pages=Mock(side_effect=[[], [{"id": "capacity", "state": "Inactive"}]]),
                             request=Mock(return_value={"capacityId": "capacity"}))
    with pytest.raises(RuntimeError, match="no run submitted or capacity changed"):
        start(client, bindings, source)
    assert [call.args[0] for call in client.request.call_args_list] == ["GET"]


def test_pipeline_start_posts_one_explicit_parameter_request():
    from instructor.run_pipeline import ROOT, start

    bindings = {"synthetic_only": True, "workspace": "00000000-0000-4000-8000-000000000001",
                "pipeline": "00000000-0000-4000-8000-000000000002"}
    source = "synthetic_834.edi" if (ROOT / "src" / "parse_834.py").exists() else None
    client = SimpleNamespace(pages=Mock(side_effect=[[], [{"id": "capacity", "state": "Active"}]]),
                             request=Mock(side_effect=[{"capacityId": "capacity"}, {"status": "Accepted"}]))
    assert start(client, bindings, source) == {"status": "Accepted"}
    request = client.request.call_args.args
    assert request[0] == "POST"
    assert request[1].endswith("?jobType=Pipeline")
    assert request[2] == {"executionData": {"parameters": {"source_file": source} if source else {}}}
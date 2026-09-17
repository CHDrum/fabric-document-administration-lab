import pytest

from instructor.fabric import api_url, ensure_items, sql_batches, upload_verified


def test_raw_upload_is_immutable_and_identical_replay_is_safe(tmp_path):
    from unittest.mock import Mock
    from azure.core.exceptions import ResourceExistsError

    source = tmp_path / "synthetic.edi"
    source.write_bytes(b"synthetic-only")
    target = Mock()
    assert upload_verified(target, source) == "Uploaded"
    assert target.upload_data.call_args.kwargs == {
        "overwrite": True, "if_none_match": "*"}
    target.upload_data.side_effect = ResourceExistsError("exists")
    target.download_file.return_value.chunks.return_value = [b"synthetic-", b"only"]
    assert upload_verified(target, source) == "Unchanged"
    target.download_file.return_value.chunks.return_value = [b"different"]
    with pytest.raises(ValueError, match="different bytes"):
        upload_verified(target, source)


def test_api_host_is_pinned():
    assert api_url("/v1/capacities") == "https://api.fabric.microsoft.com/v1/capacities"
    assert api_url("https://api.fabric.microsoft.com/v1/operations/test") == (
        "https://api.fabric.microsoft.com/v1/operations/test")


@pytest.mark.parametrize("path", ["https://example.com/v1/items", "/not-v1/items",
                                 "https://api.fabric.microsoft.com@evil.example/v1/items"])
def test_unexpected_hosts_and_versions_are_rejected(path):
    with pytest.raises(ValueError):
        api_url(path)


def test_client_go_batch_separator():
    assert sql_batches("SELECT 1;\nGO\nSELECT 'GO';\ngo\n") == ["SELECT 1;", "SELECT 'GO';"]


def test_items_do_not_overwrite_name_collisions():
    from unittest.mock import Mock

    client = Mock()
    client.pages.return_value = [{"displayName": "Landing", "type": "Notebook", "id": "existing"}]
    with pytest.raises(ValueError, match="collision"):
        ensure_items(client, "workspace", [{"displayName": "Landing", "type": "Lakehouse"}])
    client.request.assert_not_called()


def test_existing_items_are_not_recreated():
    from unittest.mock import Mock

    item = {"displayName": "Landing", "type": "Lakehouse", "id": "existing"}
    client = Mock()
    client.pages.return_value = [item]
    assert ensure_items(client, "workspace", [item])[0]["result"]["id"] == "existing"
    client.request.assert_not_called()
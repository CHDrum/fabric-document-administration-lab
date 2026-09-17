"""Instructor-only Fabric operations using the existing Azure CLI sign-in."""

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from urllib.parse import urlparse


FABRIC_ROOT = "https://api.fabric.microsoft.com"


def api_url(path):
    url = path if path.startswith("https://") else f"{FABRIC_ROOT}/{path.lstrip('/')}"
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.netloc != "api.fabric.microsoft.com"
            or not parsed.path.startswith("/v1/")):
        raise ValueError("Only the documented Fabric v1 API host is allowed")
    return url


def sql_batches(text):
    return [batch.strip() for batch in re.split(r"(?im)^\s*GO\s*;?\s*$", text) if batch.strip()]


def upload_verified(target, source, replace=False):
    from azure.core.exceptions import ResourceExistsError, ResourceModifiedError

    try:
        with source.open("rb") as content:
            conditions = {} if replace else {"if_none_match": "*"}
            target.upload_data(content, overwrite=True, **conditions)
        return "Uploaded"
    except (ResourceExistsError, ResourceModifiedError):
        if replace:
            raise
        with source.open("rb") as content:
            expected = hashlib.file_digest(content, "sha256").hexdigest()
        actual = hashlib.sha256()
        for chunk in target.download_file().chunks():
            actual.update(chunk)
        if actual.hexdigest() != expected:
            raise ValueError("Existing file has different bytes; choose a new source filename or snapshot") from None
        return "Unchanged"


def ensure_items(client, workspace, definitions):
    existing = list(client.pages(f"/v1/workspaces/{workspace}/items"))
    results = []
    for definition in definitions:
        if "creationPayload" in definition and "definition" in definition:
            raise ValueError("creationPayload and definition are mutually exclusive")
        matches = [item for item in existing if item["displayName"] == definition["displayName"]]
        if matches:
            if len(matches) != 1 or matches[0]["type"] != definition["type"]:
                raise ValueError("Item name collision; no existing item was replaced")
            result = matches[0]
        else:
            result = client.request("POST", f"/v1/workspaces/{workspace}/items", definition)
        results.append({"displayName": definition["displayName"], "result": result})
    return results


class FabricClient:
    def __init__(self):
        import requests
        from azure.identity import AzureCliCredential
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        self.credential = AzureCliCredential(process_timeout=60)
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 502, 503, 504],
                      allowed_methods=["GET"], respect_retry_after_header=True)
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def request(self, method, path, body=None):
        token = self.credential.get_token(f"{FABRIC_ROOT}/.default").token
        response = self.session.request(
            method, api_url(path), json=body, timeout=(30, 180),
            headers={"Authorization": f"Bearer {token}"}, allow_redirects=False,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Fabric HTTP {response.status_code}: {response.text[:2000]}")
        if 300 <= response.status_code < 400:
            raise RuntimeError("Unexpected redirect; credentials were not forwarded")
        result = response.json() if response.content else {}
        if response.status_code == 202:
            result = {"status": "Accepted", "operationLocation": response.headers.get("Location"),
                      "operationId": response.headers.get("x-ms-operation-id"),
                      "retryAfterSeconds": response.headers.get("Retry-After"), "body": result}
        return result

    def pages(self, path):
        while path:
            page = self.request("GET", path)
            yield from page.get("value", [])
            path = page.get("continuationUri")
            if not path and page.get("continuationToken"):
                raise RuntimeError("Continuation token without URI; use the documented next-page request")

    def sql(self, workspace, warehouse, text):
        import pyodbc

        item = self.request("GET", f"/v1/workspaces/{workspace}/warehouses/{warehouse}")
        host = item["properties"]["connectionString"]
        if not host.endswith(".datawarehouse.fabric.microsoft.com") or any(
                character in host for character in ";{}\r\n"):
            raise ValueError("Unexpected Warehouse SQL endpoint")
        database = item["displayName"].replace("}", "}}")
        token_bytes = self.credential.get_token("https://database.windows.net/.default").token.encode("utf-16-le")
        token = struct.pack("<I", len(token_bytes)) + token_bytes
        connection = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={host};DATABASE={{{database}}};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;",
            attrs_before={1256: token}, autocommit=True,
        )
        results = []
        try:
            connection.timeout = 300
            cursor = connection.cursor()
            for batch in sql_batches(text):
                cursor.execute(batch)
                while True:
                    if cursor.description:
                        columns = [column[0] for column in cursor.description]
                        results.append([dict(zip(columns, row, strict=True)) for row in cursor.fetchall()])
                    if not cursor.nextset():
                        break
        finally:
            connection.close()
        return results

    def upload(self, workspace, lakehouse, source, destination, replace=False):
        from azure.storage.filedatalake import DataLakeServiceClient

        if not destination.startswith("Files/") or ".." in Path(destination).parts:
            raise ValueError("Uploads must target a relative Lakehouse Files path")
        if replace and {"raw", "document-demo"} & set(Path(destination).parts):
            raise ValueError("Raw sources and document snapshots cannot be replaced")
        service = DataLakeServiceClient("https://onelake.dfs.fabric.microsoft.com", self.credential,
                                       api_version="2021-06-08")
        filesystem = service.get_file_system_client(workspace)
        uploaded = []
        sources = sorted(source.iterdir()) if source.is_dir() else [source]
        try:
            for local in sources:
                if not local.is_file():
                    continue
                target = f"{lakehouse}/{destination.rstrip('/')}/{local.name}"
                status = upload_verified(filesystem.get_file_client(target), local, replace)
                uploaded.append({"file": local.name, "bytes": local.stat().st_size, "destination": target, "status": status})
        finally:
            service.close()
        return uploaded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    request = subcommands.add_parser("api")
    request.add_argument("method", choices=["GET", "POST", "PATCH"])
    request.add_argument("path")
    request.add_argument("--body", type=Path)
    request.add_argument("--save", type=Path)
    workspace = subcommands.add_parser("workspace")
    workspace.add_argument("--name", required=True)
    workspace.add_argument("--capacity", required=True)
    items = subcommands.add_parser("items")
    items.add_argument("--workspace", required=True)
    items.add_argument("--manifest", type=Path, required=True)
    upload = subcommands.add_parser("upload")
    upload.add_argument("--workspace", required=True)
    upload.add_argument("--lakehouse", required=True)
    upload.add_argument("--source", type=Path, required=True)
    upload.add_argument("--destination", required=True)
    upload.add_argument("--replace", action="store_true", help="Replace code/config only; raw sources remain immutable")
    query = subcommands.add_parser("sql")
    query.add_argument("--workspace", required=True)
    query.add_argument("--warehouse", required=True)
    sql_source = query.add_mutually_exclusive_group(required=True)
    sql_source.add_argument("--file", type=Path)
    sql_source.add_argument("--query")
    query.add_argument("--assert-empty", action="store_true")
    arguments = parser.parse_args()
    client = FabricClient()
    if arguments.command == "workspace":
        capacities = list(client.pages("/v1/capacities"))
        capacity = next((item for item in capacities if item["id"] == arguments.capacity), None)
        if not capacity or capacity["state"] != "Active":
            raise RuntimeError("The requested capacity is not accessible and Active; no changes made")
        matches = [item for item in client.pages("/v1/workspaces") if item["displayName"] == arguments.name]
        if matches:
            result = {"status": "AlreadyExists", "workspaces": matches}
        else:
            result = client.request("POST", "/v1/workspaces", {
                "displayName": arguments.name, "capacityId": arguments.capacity,
                "description": "Fabric synthetic workshop demo. No production data.",
            })
    elif arguments.command == "items":
        manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
        result = ensure_items(client, arguments.workspace, manifest["foundation_items"])
    elif arguments.command == "upload":
        result = client.upload(arguments.workspace, arguments.lakehouse, arguments.source, arguments.destination, arguments.replace)
    elif arguments.command == "sql":
        text = arguments.file.read_text(encoding="utf-8") if arguments.file else arguments.query
        result = client.sql(arguments.workspace, arguments.warehouse, text)
        if arguments.assert_empty and any(result):
            raise RuntimeError(f"SQL validation returned failure rows: {json.dumps(result, default=str)}")
    else:
        body = json.loads(arguments.body.read_text(encoding="utf-8")) if arguments.body else None
        result = client.request(arguments.method, arguments.path, body)
        if arguments.save:
            arguments.save.parent.mkdir(parents=True, exist_ok=True)
            arguments.save.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
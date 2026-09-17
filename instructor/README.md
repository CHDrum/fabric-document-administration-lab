# Instructor Runbook | Document Administration

This repository is independently usable. All inputs and outputs are fabricated. The learner route is the [seven-module portal guide](../lab-guide/README.md); local tools below are optional instructor tools, never learner prerequisites.

## Workshop Delivery

Plan for 10-15 Fabric beginners, preferably paired, in **your tenant and approved capacity**. Use unique workspace names per pair and stagger starts. Provision and validate your own instructor workspace before delivery. Capacity headroom and a timed beginner rehearsal must be checked for each workshop.

| Session | Minutes |
| --- | ---: |
| Orientation, tenant check, finished-product tour | 20 |
| Document modules: 10 / 25 / 25 / 25 / 30 / 10 / 5 | 130 |
| Break | 20 |
| 834 modules: 10 / 20 / 30 / 30 / 25 / 10 / 5 | 130 |
| Review, ownership, and production gates | 30 |
| Total, excluding optional 30-minute buffer | 330 |

Ten-minute tour within orientation: spend two minutes on the illustrative scenario, two on catalog/revisions/ownership, two on job cost and invoice reconciliation, two on the 834 health/findings example, and two on human review and production boundaries. Use your validated reports. Test author rendering and audience access separately.

Before class, verify repository ZIP download for every learner, permitted workspace creation, Fabric item authoring, Warehouse SQL access, and eligible individual Power BI licenses. Authenticate to GitHub if repository visibility requires it. Fabric capacity does not provide individual author/viewer licenses; below-F64 viewing has separate requirements. Repository access does not grant tenant access.

## Lab Items

No hosted workspace or deployed bindings are distributed. Start with [bindings.example.json](bindings.example.json) and create these items in an approved workspace. Keep actual IDs and endpoints in an ignored local binding file.

| Item | Display Name |
| --- | --- |
| Lakehouse | DocumentLanding |
| Warehouse | DocumentProducts |
| Pipeline | DocumentIngestion |
| Explicit Direct Lake model | DocumentAnalytics |
| Report | Fabric Document Administration |

Confirm current capacity availability and licenses with the capacity owner. No SKU, region, or concurrency allowance is guaranteed by this lab. See [validation status](../docs/validation-status.md). Do not buy, resize, pause, resume, or delete shared capacity as a workshop recovery step.

## Optional Instructor Setup

Use Python 3.11, Azure CLI already authenticated to the approved tenant, and Microsoft ODBC Driver 18 for SQL Server. The helper obtains short-lived tokens using `AzureCliCredential`; no tokens or passwords belong in bindings, logs, Git, or screenshots. Confirm that your selected interpreter contains the dependencies.

From this repository's root in PowerShell:

```powershell
py -3.11 -m venv "$env:TEMP\fabric-document-instructor"
& "$env:TEMP\fabric-document-instructor\Scripts\python.exe" -m pip install -r requirements-dev.txt -r instructor/requirements.txt
& "$env:TEMP\fabric-document-instructor\Scripts\python.exe" -m pytest tests -q -p no:cacheprovider
```

Optional report-browser verification requires `playwright==1.58.0` and its Chromium browser. Install that package in the same instructor environment and run `python -m playwright install chromium` before using the report verifier below.

## New Workspace Deployment

Perform these steps in one new, approved workspace; never run target-creation instructions blindly against an existing environment.

1. Create and assign the workspace to the approved capacity in the Fabric portal. Create `DocumentLanding` and `DocumentProducts`. Follow [landing](../lab-guide/01-landing.md) to upload all six CSVs under `Files/document-demo/DOCUMENT-DEMO-001`. Files are not Delta tables.
2. Run [schema SQL](../sql/01_warehouse_schema.sql), then [publication SQL](../sql/02_catalog_and_cost_products.sql) in the Warehouse editor. These create objects, not published data. Do not replace source-system SSRS procedures.
3. Create the six sequential Copy activities and final publication Script exactly as [ingestion](../lab-guide/02-ingestion.md) and [products](../lab-guide/03-products.md) describe. Choose Workspace staging. No notebook, Environment, Spark pool, external connection, or gateway is needed for these synthetic files.
4. Run the pipeline once, wait for completion, then run [acceptance SQL](../sql/03_validate.sql). An empty result is the pass condition. Inspect all activity results rather than just pipeline creation status.
5. Create the explicit model over the seven physical tables, aliases, four one-to-many relationships, and measures in the [generated reference](../solution/portable/measures.md). Do not select SQL views as Direct Lake partitions.
6. Create the three report pages using [the report guide](../lab-guide/04-report.md). Test rendering, filtering, and refresh in the browser under both the author and an approved non-owner. These tests are not replaced by model-query success.

### Request Packaging and Rebinding

[bindings.example.json](bindings.example.json) contains placeholder IDs and a placeholder Warehouse endpoint. Copy it to `instructor/bindings.local.json` and supply the new workspace, Lakehouse, Warehouse, SQL host/database, and explicit semantic-model ID. Every target ID must belong to the new workspace. Model ID is only known after model creation; regenerate the package before report creation. [package_solution.py](package_solution.py) does not create resources.

```powershell
python instructor/package_solution.py --bindings instructor/bindings.example.json --output solution/portable
```

For deployment, use `--bindings instructor/bindings.local.json --output solution/deployed`. Keep that generated folder private and ignored. The three generated requests are sent separately to `POST /v1/workspaces/{workspace}/items`. For an existing item use its `updateDefinition` endpoint with only the request's `definition` object; never send both `creationPayload` and `definition`. A pipeline request must bind the new Lakehouse and Warehouse; the model must bind the new Warehouse host/database; the report must bind the new semantic model. No cross-workspace ID should survive a rebind.

An `Accepted` export is only an operation receipt: retrieve its canonical `/v1/operations/{operationId}/result` after the operation succeeds. Treat exports as potentially sensitive configuration and keep them out of the distributable repository. Package generation or an exported definition alone does not prove a successful deployment.

For supported commands and exact flags use `python instructor/fabric.py --help` and its subcommand help. Two read-only/validation examples, substituting approved target IDs:

```powershell
python instructor/fabric.py sql --workspace WORKSPACE_UUID --warehouse WAREHOUSE_UUID --file sql/03_validate.sql --assert-empty
python instructor/fabric.py api GET /v1/workspaces/WORKSPACE_UUID/items/PIPELINE_UUID/jobs/instances
```

GET requests alone have bounded transient retries. For a mutation with an ambiguous response, list items or inspect the accepted operation before retrying. Respect 429/Retry-After. Do not start a second pipeline to resolve uncertainty about the first.

## Acceptance, Replay, and Recovery

Use a single operator and one active pipeline per lab workspace. Shared staging/latest tables have **no cross-run lease**. Listing active runs is a preflight, not atomic concurrency control. Disable schedules and coordinate people before a probe.

The [expected input/result contract](../data/sample/expected.json), [data dictionary](../docs/data-dictionary.md), and [requirements matrix](../docs/requirements-traceability.md) explain the checks: 22 SQL assertions, 16 DAX measures, replay, and a controlled failed publication. Run these checks in your own environment. Verify all three report pages, displayed values and filter/reset separately. Approved non-owner access is a separate acceptance gate.

```powershell
python instructor/verify_solution.py --bindings instructor/bindings.local.json --replay --failure-probe
```

For a separate authenticated report check with the optional Playwright installation, run `python instructor/verify_report.py --workspace WORKSPACE_UUID --report REPORT_UUID --output docs/images/report`, substituting the intended target IDs. It checks visible pages, displayed card values, filtering and reset, and saves synthetic screenshots without persisting tokens or browser state. The current report package uses PBIR file format 4.0 with internal report definition version 2.0.0; these are distinct version fields.

The data verifier requires `synthetic_only: true` and pipeline/warehouse/model/workspace IDs. It refuses active pipeline jobs, checks the small fixture, republishes without duplicating products, then temporarily sets synthetic J001's staging quantity to `NOT-A-NUMBER`. The expected validation guard blocks publication. The runner compares the successful product snapshot before/after and restores the original staging quantity in `finally`. Failed audit entries are deliberately retained. It queries every model measure; unit cost is fixed-decimal `0.8231`, and the illustrative 5% amount is `436.25`.

If a process is forcibly interrupted during the failure probe, inspect `stg_jobs` and restore the six CSV staging tables using the pipeline before publishing. If a Copy fails, fix its path/schema/destination/staging setting and rerun the serialized pipeline; publication does not begin until all six Copies succeed. A failed SQL publication must leave the previous published snapshot intact. Do not delete audit history to make a run appear clean.

Source upload is conditional create plus byte-hash comparison on replay. Differing bytes at an existing raw path are refused. This is a helper behavior, not WORM storage, authorization, or a production retention policy. Use a new approved snapshot/path for changed inputs; the frozen six-file lab acceptance is not a general production loader.

## Handoff and Production Gates

Send the small team the module answer keys, dictionary, traceability matrix, exact pipeline/model/report bindings, latest successful run and publication attempt IDs, and an explicit owner list. Name a source owner, product owner, rule/reconciliation approver, platform operator, and report owner. Do not infer access from an administrator's successful query.

Future enterprise integration requires approved acquisition contracts for operational applications, content platforms, fulfillment providers, and financial systems. Agree refresh cadence, source keys/history, vendor reconciliation, retention, privacy and export controls, support, concurrency, recovery and enterprise data warehouse partnership. Preserve operational workflows. Only the catalog and reconciliation teaching slices are implemented here, not all seven document subjects.

No synthetic variance or scenario proves achieved savings. Cleanup is limited to specifically approved learner workspaces after their exports and retention review; preserve shared capacity and other owners' workspaces.
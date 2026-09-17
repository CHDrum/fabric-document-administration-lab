# 02 - Build Ingestion

**Duration:** 25 minutes

**Objective:** load the snapshot predictably without multiplying rows on replay.

## Configure the First Copy

1. In the workspace create a **Data pipeline** named `DocumentIngestion`. Add a **Copy data** activity and name it `Copy_documents`.
2. On **Source**, select your workspace's Lakehouse `DocumentLanding`, choose **Files**, and select `document-demo/DOCUMENT-DEMO-001/documents.csv`. Choose **Delimited text**, comma delimiter, UTF-8, first row as header, double-quote quote character, and backslash escape character. Use newline as the row delimiter. Do not enable recursion or partition discovery.
3. On **Destination**, select your workspace's Warehouse `DocumentProducts`, **Use existing** table, `dbo.stg_documents`, and **Insert** write behavior. Under advanced options set **Pre-copy script** to:

```sql
DELETE FROM dbo.stg_documents;
```

4. On **Mapping**, import schemas and map each named CSV column to its identically named destination column. The source data goes into string staging columns so validation can inspect bad values later. Do not silently truncate data or skip incompatible rows.
5. On **Settings**, select **Enable staging > Workspace**. Do not create an external staging account or add credentials. This uses Fabric-managed temporary staging for the Warehouse COPY operation.

## Complete the Sequence

6. Duplicate the Copy activity five times, or create each with the same settings. Change the name, source file, destination table, pre-copy script, and imported mapping for each row below. A copied activity's old mapping must not remain attached to the new file.

| Activity name | Filename | Destination / pre-copy target |
| --- | --- | --- |
| Copy_documents | documents.csv | dbo.stg_documents |
| Copy_revisions | revisions.csv | dbo.stg_revisions |
| Copy_jobs | jobs.csv | dbo.stg_jobs |
| Copy_vendors | vendors.csv | dbo.stg_vendors |
| Copy_cost_centers | cost_centers.csv | dbo.stg_cost_centers |
| Copy_invoice_lines | invoice_lines.csv | dbo.stg_invoice_lines |

7. Connect each activity's green **Succeeded** output to the next activity in the table. Do not use Completed or parallel branches. There must be a single chain of six activities.
8. Save, validate, and run once. Use the **Output** pane or Monitoring hub to inspect each activity. Wait for completion; do not press Run again while it is active.
9. In the Warehouse, run this query and compare it with Module 01's row counts:

```sql
SELECT 'documents' AS source_name, COUNT_BIG(*) AS row_count FROM dbo.stg_documents
UNION ALL SELECT 'revisions', COUNT_BIG(*) FROM dbo.stg_revisions
UNION ALL SELECT 'jobs', COUNT_BIG(*) FROM dbo.stg_jobs
UNION ALL SELECT 'vendors', COUNT_BIG(*) FROM dbo.stg_vendors
UNION ALL SELECT 'cost_centers', COUNT_BIG(*) FROM dbo.stg_cost_centers
UNION ALL SELECT 'invoice_lines', COUNT_BIG(*) FROM dbo.stg_invoice_lines;
```

## Completion Checklist

- [ ] Six copies succeeded and counts are 6, 8, 7, 3, 3, 13.
- [ ] Header names are not data rows; `NOT-A-NUMBER` is still a string in staging.
- [ ] Each activity deletes only its own staging table before inserting.
- [ ] No schedule and no second operator can start a concurrent lab run by agreement.

## Challenge and Answer

**Question:** Why delete staging but preserve raw files?

**Answer:** Staging is replaceable per-run working data. The preserved source snapshot supports replay and investigation. Pre-copy deletion prevents append duplication; it is not a transaction across all six copies and is not a cross-run lock.

## Recovery

For a missing source file, check the selected Lakehouse, Files/Table choice, path and case. For COPY or unsupported-format errors, verify **Workspace staging**, existing string staging tables, headers and mappings. Inspect the failed activity before rerunning the whole serialized chain. A partial copy does not publish products. The verified builder is [build_pipeline.py](../solution/build_pipeline.py); its JSON requests are instructor/API artifacts, not a promise of a portal JSON-import command.

[Previous: Landing](01-landing.md) | [Guide](README.md) | [Next: Publish products](03-products.md)
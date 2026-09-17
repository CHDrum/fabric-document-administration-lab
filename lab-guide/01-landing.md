# 01 - Land the Snapshot

**Duration:** 25 minutes

**Objective:** preserve a synthetic source snapshot in OneLake Files and prepare a typed Warehouse publication boundary.

## Steps

1. In your lab workspace choose **New item > Lakehouse** and name it `DocumentLanding`. Use the item search if the creation menu is organized differently.
2. Open the Lakehouse **Files** area. Create folders `document-demo` and, within it, `DOCUMENT-DEMO-001`.
3. Use **Upload > Upload files** to upload the six CSVs from [data/sample](../data/sample). Upload the files listed below, not the whole repository or the expected-results JSON. Preserve the headers, names, and bytes. If the portal asks to overwrite an existing file, cancel and verify the existing snapshot instead.
4. Return to the workspace and create a **Warehouse** named `DocumentProducts`. It is a separate item from the Lakehouse's automatically associated SQL analytics endpoint.
5. Open `DocumentProducts`, choose **New SQL query**, and paste the complete contents of [01_warehouse_schema.sql](../sql/01_warehouse_schema.sql). Run all batches. Keep `GO` on its own line. Refresh the object explorer.
6. Confirm the six `dbo.stg_...` tables and empty product tables exist. This script is rerunnable and does not load or publish data. Do not run it in the Lakehouse SQL analytics endpoint, which is not the writable Warehouse used by this lab.

| Source file | Rows excluding header | Grain | Warehouse destination |
| --- | ---: | --- | --- |
| documents.csv | 6 | One document item | dbo.stg_documents |
| revisions.csv | 8 | One revision of an item | dbo.stg_revisions |
| jobs.csv | 7 | One production job | dbo.stg_jobs |
| vendors.csv | 3 | One vendor | dbo.stg_vendors |
| cost_centers.csv | 3 | One cost center | dbo.stg_cost_centers |
| invoice_lines.csv | 13 | One received invoice line | dbo.stg_invoice_lines |

The destination path is `Files/document-demo/DOCUMENT-DEMO-001`. In a Copy source that already selects **Files**, its relative folder is `document-demo/DOCUMENT-DEMO-001`, without repeating `Files/`.

## Completion Checklist

- [ ] Both items exist in the learner workspace, with the exact item names above.
- [ ] All six files are visible under the snapshot folder.
- [ ] Warehouse staging tables exist and are empty.
- [ ] No Spark session, Dataflow, external storage account, gateway, or production connector was required.

## Challenge and Answer

**Question:** Should the CSVs appear under Lakehouse Tables after upload?

**Answer:** No. Files and Delta Tables are different surfaces. The document pipeline reads Files directly and writes Warehouse staging. No CSV-to-Delta notebook is needed.

## Recovery

If a filename differs, correct the upload selection before building ingestion. If a table is missing, make sure every SQL batch ran against `DocumentProducts` and that your account can create Warehouse objects. Do not fix a staging failure by editing the raw data; the deliberately bad invoice values are required for later review exercises.

[Previous: Start](00-start.md) | [Guide](README.md) | [Next: Build ingestion](02-ingestion.md)
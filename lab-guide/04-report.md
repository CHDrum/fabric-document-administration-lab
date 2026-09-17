# 04 - Create the Model and Report

**Duration:** 30 minutes

**Objective:** make catalog and finance definitions reusable in Power BI, with optional eligible Excel consumption.

## Create an Explicit Model

1. In the Warehouse ribbon select **New semantic model**. Name it `DocumentAnalytics`, save it in your lab workspace, and select only the physical tables in the mapping below. Do not select views or assume that a Warehouse already has a default model.
2. Open the model with **Open data model**. Rename its table display names to the aliases below without changing their source bindings.

| Physical Warehouse table | Model alias |
| --- | --- |
| report_catalog | Catalog |
| dim_revision | Revision |
| fact_job_cost | Jobs |
| dim_vendor | Vendor |
| dim_cost_center | CostCenter |
| report_reconciliation | Reconciliation |
| invoice_disposition | InvoiceReview |

3. Use Model view to create the four relationships below. Keep filtering **single direction from one to many**. Inspect automatically suggested relationships; remove any that contradict this list. Leave Reconciliation and InvoiceReview disconnected from job filters.

| One side | Many side |
| --- | --- |
| Catalog.document_id | Jobs.document_id |
| Catalog.document_id | Revision.document_id |
| Vendor.vendor_id | Jobs.vendor_id |
| CostCenter.cost_center_id | Jobs.cost_center_id |

4. From **New measure**, add the DAX definitions and formats in [the measure reference](../solution/portable/measures.md) to their listed home tables. Begin with Catalog Items, Current Publications, Missing Owners, Matched Job Spend, Produced Units, Cost Variance, Source Parseable Amount, and Unparseable Lines; then add the remaining reference measures. Set identifier columns to **Don't summarize**. Retain Direct Lake over the physical products.

## Build Three Pages in the Browser

5. Choose **New report** from web modeling. Save it in your workspace as `Fabric Document Administration`. The exact web editing labels can vary by tenant release; no Power BI Desktop import is required.
6. Create the following pages using standard cards, tables, a bar chart, and a slicer. Select fields from the model, not imported local CSVs. Resize visuals to avoid overlap and give the report an accessible title and useful alt text.

| Page | Visuals and fields | Expected unfiltered result |
| --- | --- | --- |
| Catalog | Cards: Catalog Items, Current Publications, Missing Owners. Table: document_id, title, owner, business_status, current_revision_id. Slicer: business_status. | 6 items, 4 current, 1 missing owner |
| Spend | Cards: Matched Job Spend, Produced Units, Cost Variance. Bar chart: Vendor.vendor_name and Matched Job Spend. Table: Jobs.job_id, quantity, expected_cost, actual_cost, variance. | $8,725; 10,600; $275 |
| Reconciliation | Cards: Source Parseable Amount and Unparseable Lines. Table: Reconciliation.disposition, line_count, parseable_amount, unparseable_count. Table: InvoiceReview source_line_id, job_id, raw_amount, disposition, reason. | $11,305; one unparseable line; all review buckets visible |

7. Clear all slicers and verify the totals. Filter a vendor on Spend and confirm the job-grain measure changes without multiplying rows. Reconciliation is intentionally disconnected: do not imply its file-wide buckets are filtered by the vendor or cost-center slicer.
8. Save, reopen the report from the workspace, and verify every visual in **your own** browser. Record any rendering or permissions failure separately from SQL/model-query success. Check all three pages, displayed values, filtering, and reset, then test approved non-owner access separately.

## Optional Excel Consumption

With an eligible Excel client, account license, tenant settings and semantic-model **Build** permission, use the semantic model's **Analyze in Excel** or Excel's Power BI semantic-model connection. Build a pivot by vendor with Matched Job Spend. This is an optional consumer exercise, not a workshop installation prerequisite. The same measure definition should produce the same unfiltered $8,725 total. Do not export raw records to bypass a permission failure.

## Challenge and Answer

**Question:** Does the illustrative 5% measure prove savings?

**Answer:** No. It equals $436.25 against synthetic matched spend. It is an illustrative scenario, not a forecast or achieved savings.

## Completion and Recovery

- [ ] Explicit model, table aliases, relationships and measures saved.
- [ ] Three report pages saved, reopened and personally checked, or a precise rendering limitation recorded.
- [ ] No Publish to web or public sharing.

If model creation opens no editor, inspect the browser's pop-up blocker. If measures show errors, verify aliases and physical source tables. If data appears stale after publication, refresh/reframe the semantic model through its supported refresh action and recheck; do not load a second CSV copy into the report. Missing Build or viewing permissions requires the workspace/model owner and may also involve an individual license.

[Previous: Products](03-products.md) | [Guide](README.md) | [Next: Validate and replay](05-validate.md)
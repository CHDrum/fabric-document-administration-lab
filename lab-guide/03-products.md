# 03 - Publish Catalog and Cost Products

**Duration:** 25 minutes

**Objective:** publish an item/revision catalog and reconciled job-grain cost products, with review exceptions kept visible.

## Steps

1. In the `DocumentProducts` Warehouse SQL editor, paste and run all of [02_catalog_and_cost_products.sql](../sql/02_catalog_and_cost_products.sql). This defines the publication procedure and views; it does not replace operational applications or invoke an on-premises workflow.
2. After the six copies have completed, publish the teaching snapshot explicitly:

```sql
EXEC dbo.publish_document_products
    @snapshot_id = 'DOCUMENT-DEMO-001',
    @as_of_date = '2027-01-01';
```

3. Inspect the current and historical products:

```sql
SELECT * FROM dbo.v_current_catalog ORDER BY document_id;
SELECT * FROM dbo.v_catalog_history WHERE document_id = 'D001';
SELECT * FROM dbo.fact_job_cost ORDER BY job_id;
SELECT * FROM dbo.report_reconciliation ORDER BY disposition;
SELECT * FROM dbo.invoice_disposition WHERE disposition <> 'Matched' ORDER BY source_line_id;
```

4. Confirm D001 retains retired revision R001 and current R002. D003 has current R004 and future draft R008. D005 is archived. D006 has missing ownership and a proposed/future revision, not a current publication. Four publications are current as of the fixed teaching date.
5. Add a **Script** activity named `Publish_products` to `DocumentIngestion`. Select the same Warehouse connection. Add a **NonQuery** script containing `EXEC dbo.publish_document_products;`. Connect `Copy_invoice_lines` **Succeeded** to it. Save the pipeline. The procedure defaults to the same snapshot and as-of date used above.
6. Rerun the complete pipeline only after confirming no other run is active. Verify `Publish_products` succeeds. This is now the complete acquisition-to-publication sequence.

## Product Contracts

| Product | Grain / purpose |
| --- | --- |
| dim_document / report_catalog | One document item, ownership and current-state publication |
| dim_revision / v_catalog_history | Retained revision history, not one record per document |
| invoice_disposition | One source line with Matched, Unmatched, or Rejected disposition |
| fact_invoice | Accepted parsed invoice facts with disposition retained |
| fact_job_cost | One job with invoice amounts aggregated before joins |
| report_reconciliation | One disposition bucket and unparseable count |
| publication_history | One publication attempt with success/failure information |

## Answer Key

| Check | Expected |
| --- | --- |
| Parseable source | $11,305.00 |
| Matched | 9 lines, $8,725.00 |
| Unmatched | 2 lines, $480.00 |
| Rejected | 2 lines, $2,100.00 parseable plus one unparseable value |
| Job quantity / expected / actual / variance | 10,600 / $8,450 / $8,725 / $275 |

L008 references unknown job J999 ($400). L009 duplicates L001 ($2,100). L010 contains `NOT-A-NUMBER`. L013 mismatches the vendor for J001 ($80). Credit L007 remains -$100. J001's net spend is $2,000, and J003 is $3,250, including a second $50 line.

## Challenge and Answer

**Question:** Why not join invoice lines directly to all catalog revisions and then sum?

**Answer:** The joins can multiply invoice or job values across revision rows. Aggregate invoice amounts at job grain first, retain unique item and reference dimensions, and expose history separately. Reconciliation must include unmatched and rejected values rather than hiding them in a filtered total.

## Completion and Recovery

- [ ] Current catalog, history, and every review bucket match the answer key.
- [ ] Publication executes only after all copies succeed.
- [ ] The procedure's validation/transaction boundary protects previously published products on failure; staging itself is replaceable.

If a validation guard raises an error, inspect staging counts, duplicate keys and references. Restore the original six CSVs through the pipeline, not by deleting validation rules. This is a frozen reference contract, not a generic loader for arbitrary source volumes.

[Previous: Ingestion](02-ingestion.md) | [Guide](README.md) | [Next: Model and report](04-report.md)
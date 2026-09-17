# 05 - Validate and Replay

**Duration:** 10 minutes

**Objective:** distinguish a repeatable, reconciled publication from a pipeline that merely reports success.

## Steps

1. In the Warehouse run all of [03_validate.sql](../sql/03_validate.sql). The result is a list of failures: **zero returned rows is success**. The reference checks include counts, current versus historical revisions, exact financial buckets, credits and job-grain totals.
2. Check the full result contract in [expected.json](../data/sample/expected.json). Do not change expected values to fit an unexpected result.
3. With no pipeline active, run `EXEC dbo.publish_document_products;` again. Re-run the same acceptance SQL. Product counts and money should be unchanged while publication history records a new attempt.
4. Inspect the attempt history:

```sql
SELECT attempt_id, snapshot_id, publication_status, published_at, source_line_count, message
FROM dbo.publication_history ORDER BY published_at DESC;
```

5. Reopen the report, clear all filters, and compare the model totals below. If required, refresh the semantic model after publication. Record report rendering separately from data checks.

| Measure | Expected |
| --- | ---: |
| Catalog Items / Current Publications / Missing Owners | 6 / 4 / 1 |
| Catalog Coverage / Revision Count | 66.7% / 8 |
| Matched Job Spend / Expected Job Cost / Cost Variance | $8,725 / $8,450 / $275 |
| Cost Per Produced Unit | $0.8231 |
| Source Parseable Amount / Unmatched Amount | $11,305 / $480 |
| Rejected Parseable Amount / Unparseable Lines | $2,100 / 1 |
| Illustrative 5 Percent Reduction | $436.25 |

## Challenge and Answer

**Question:** Why is checking only the grand total insufficient?

**Answer:** Missing rows, duplicated rows, credits and compensating errors can produce plausible totals. The acceptance script checks keys, grains, categories and specific edge cases as well as totals. An API-created report is not proof that its visuals render or that another user can access it.

## Completion and Recovery

- [ ] Acceptance SQL returned no failures before and after replay.
- [ ] Product counts did not grow, and a new publication attempt is visible.
- [ ] Model and report checks are recorded separately; unresolved checks are not marked passed.

For a failure, inspect the returned check name, compare the original source and staging rows, and rerun the serialized pipeline after repairing its configuration. Do not overwrite original CSVs or remove rejected lines. Shared staging means simultaneous runs are prohibited even though each pipeline's internal activities are sequential.

[Previous: Reporting](04-report.md) | [Guide](README.md) | [Next: Wrap up](06-wrap-up.md)
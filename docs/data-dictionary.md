# Data Dictionary | Document Administration

All values are synthetic. Keys and data types are authoritative in [schema SQL](../sql/01_warehouse_schema.sql); transformation and disposition precedence are in [publication SQL](../sql/02_catalog_and_cost_products.sql). This document describes the frozen teaching snapshot, not production source connectivity.

## Source Tables

CSV headers match the six string-typed staging tables. String staging preserves invalid amounts for review instead of silently dropping rows. Dates use ISO `YYYY-MM-DD`; empty strings mean missing values. Snapshot `DOCUMENT-DEMO-001` is evaluated at `2027-01-01`; currency is USD.

| File / Grain | Fields and Meaning | Expected Rows |
| --- | --- | ---: |
| [documents.csv](../data/sample/documents.csv): one catalog item | `document_id` stable key; `title`; `owner`; `business_status`; `document_type` | 6 |
| [revisions.csv](../data/sample/revisions.csv): one version | `revision_id` key; `document_id` parent; `revision_number`; `revision_status`; `effective_date`; optional `end_date`; optional `publication_date`; physical/digital `channel` | 8 |
| [jobs.csv](../data/sample/jobs.csv): one production job | `job_id` key; `revision_id`; `vendor_id`; `cost_center_id`; `production_date`; positive `quantity`; `expected_cost` in USD | 7 |
| [vendors.csv](../data/sample/vendors.csv): one vendor | `vendor_id` key; `vendor_name` | 3 |
| [cost_centers.csv](../data/sample/cost_centers.csv): one financial owner | `cost_center_id` key; `cost_center_name` | 3 |
| [invoice_lines.csv](../data/sample/invoice_lines.csv): one received source row | `source_line_id` key; `vendor_id`; `invoice_id`; `line_number`; `job_id`; raw `amount`; `currency` | 13 |

The invoice business key is vendor/invoice/line, distinct from the unique source row key. One job can have multiple lines and credits. Aggregate matched invoice amounts to job grain **before** joining catalog/revision details, or job quantity and expected cost can be multiplied.

## Published Products

| Table | Grain and Important Fields | Use |
| --- | --- | --- |
| `dim_document` | Item; missing owner becomes NULL; `snapshot_id` | Stable identity and accountability |
| `dim_revision` | Revision; typed version/dates; document parent; snapshot | Full physical/digital and publication history |
| `dim_vendor`, `dim_cost_center` | Vendor or financial owner | Slicing and oversight |
| `invoice_disposition` | Source row; raw and parsed amount; disposition/reason; snapshot | Traceable matched, unmatched, and rejected review |
| `fact_invoice` | Parseable invoice source row and its disposition | Financial reconciliation detail, not a second additive job table |
| `fact_job_cost` | Job; quantity BIGINT; expected/actual/variance DECIMAL(18,2); document/revision/vendor/center/channel | Cost and volume without invoice join fan-out |
| `report_catalog` | Item; selected current revision and typed dates; `has_current_publication`, `missing_owner`, as-of date and snapshot | Physical Direct Lake catalog table |
| `report_reconciliation` | Disposition; row count, parseable amount, unparseable count and snapshot | Disconnected reconciliation table |
| `publication_history` | Attempt; snapshot, status, UTC time, source count, message | Retained success/failure evidence |

`v_catalog_history` exposes all revisions; `v_current_catalog` exposes current publications; `v_cost_reconciliation` exposes financial buckets. These are SQL query surfaces, not the model's physical Direct Lake partitions. [The model reference](../solution/portable/measures.md) defines all seven aliases, measures, formats, and relationships.

## Meaning of Current

A published revision must have publication/effective dates on or before the as-of date and no expired end date. Ranking selects one eligible revision per item. The catalog retains items with no current publication rather than hiding them. D001 retains retired R001 and current R002; D003 has current R004 and future draft R008; D005 is archived; D006 has missing ownership and future proposed R007. D001-D004 are current: 4 of 6 items, or 66.67% coverage. These fixture semantics need business approval before production.

## Financial Contract

The [expected JSON](../data/sample/expected.json) and [acceptance SQL](../sql/03_validate.sql) freeze each bucket and edge case:

| Result | Value |
| --- | ---: |
| Matched: 9 lines | $8,725 |
| Unmatched: 2 lines | $480 |
| Rejected: 2 lines, one unparseable | $2,100 parseable |
| Parseable total = matched + unmatched + rejected | $11,305 |
| Produced units / expected cost / variance | 10,600 / $8,450 / $275 |
| Matched cost per produced unit, model fixed-decimal | $0.8231 |
| Illustrative 5% reduction of matched spend | $436.25 |

L008 references unknown J999 ($400); L009 duplicates L001 ($2,100); L010 contains `NOT-A-NUMBER`; L013 references J001 with a different vendor ($80). L007's -$100 credit is valid. J001 nets $2,000; J003 is $3,250 including an extra $50 line. Excluding a rejected/unmatched row from matched spend does not erase it from the source reconciliation.

This is a shared analytical data product demonstration. It does not claim complete document mastering, preference enforcement, constituent identity, delivery capture, source retention enforcement, or achieved savings. See [requirements coverage](requirements-traceability.md) for the distinction.
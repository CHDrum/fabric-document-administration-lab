# Semantic Model Reference

Generated from the same definition used for deployment. All data is synthetic.

Create an explicit Direct Lake model over these physical Warehouse tables; do not select the views.

## Catalog (dbo.report_catalog)

Columns: `document_id`, `title`, `owner`, `business_status`, `document_type`, `current_revision_id`, `revision_number`, `channel`, `publication_date`, `effective_date`, `has_current_publication`, `missing_owner`, `as_of_date`

### Catalog Items

```dax
Catalog Items = COUNTROWS('Catalog')
```
Format: `#,0`

### Current Publications

```dax
Current Publications = SUM('Catalog'[has_current_publication])
```
Format: `#,0`

### Missing Owners

```dax
Missing Owners = SUM('Catalog'[missing_owner])
```
Format: `#,0`

### Catalog Coverage

```dax
Catalog Coverage = DIVIDE([Current Publications], [Catalog Items])
```
Format: `0.0%`

## Revision (dbo.dim_revision)

Columns: `revision_id`, `document_id`, `revision_number`, `revision_status`, `effective_date`, `end_date`, `publication_date`, `channel`

### Revision Count

```dax
Revision Count = COUNTROWS('Revision')
```
Format: `#,0`

## Jobs (dbo.fact_job_cost)

Columns: `job_id`, `revision_id`, `document_id`, `vendor_id`, `cost_center_id`, `production_date`, `channel`, `quantity`, `expected_cost`, `actual_cost`, `variance`

### Job Count

```dax
Job Count = COUNTROWS('Jobs')
```
Format: `#,0`

### Produced Units

```dax
Produced Units = SUM('Jobs'[quantity])
```
Format: `#,0`

### Matched Job Spend

```dax
Matched Job Spend = SUM('Jobs'[actual_cost])
```
Format: `$#,0.00;($#,0.00)`

### Expected Job Cost

```dax
Expected Job Cost = SUM('Jobs'[expected_cost])
```
Format: `$#,0.00;($#,0.00)`

### Cost Variance

```dax
Cost Variance = SUM('Jobs'[variance])
```
Format: `$#,0.00;($#,0.00)`

### Cost Per Produced Unit

```dax
Cost Per Produced Unit = DIVIDE([Matched Job Spend], [Produced Units])
```
Format: `$0.0000`

### Illustrative 5 Percent Reduction

```dax
Illustrative 5 Percent Reduction = [Matched Job Spend] * 0.05
```
Format: `$#,0.00`

## Vendor (dbo.dim_vendor)

Columns: `vendor_id`, `vendor_name`

## CostCenter (dbo.dim_cost_center)

Columns: `cost_center_id`, `cost_center_name`

## Reconciliation (dbo.report_reconciliation)

Columns: `disposition`, `line_count`, `parseable_amount`, `unparseable_count`

### Source Parseable Amount

```dax
Source Parseable Amount = SUM('Reconciliation'[parseable_amount])
```
Format: `$#,0.00`

### Unmatched Amount

```dax
Unmatched Amount = CALCULATE(SUM('Reconciliation'[parseable_amount]), 'Reconciliation'[disposition] = "Unmatched")
```
Format: `$#,0.00`

### Rejected Parseable Amount

```dax
Rejected Parseable Amount = CALCULATE(SUM('Reconciliation'[parseable_amount]), 'Reconciliation'[disposition] = "Rejected")
```
Format: `$#,0.00`

### Unparseable Lines

```dax
Unparseable Lines = SUM('Reconciliation'[unparseable_count])
```
Format: `#,0`

## InvoiceReview (dbo.invoice_disposition)

Columns: `source_line_id`, `vendor_id`, `invoice_id`, `line_number`, `job_id`, `raw_amount`, `parsed_amount`, `currency`, `disposition`, `reason`

## Relationships

Use single-direction filtering from the one side to the many side.

- `Catalog.document_id` (one) to `Jobs.document_id` (many)
- `Catalog.document_id` (one) to `Revision.document_id` (many)
- `Vendor.vendor_id` (one) to `Jobs.vendor_id` (many)
- `CostCenter.cost_center_id` (one) to `Jobs.cost_center_id` (many)

IF OBJECT_ID('dbo.stg_documents') IS NULL
CREATE TABLE dbo.stg_documents (
    document_id VARCHAR(32), title VARCHAR(256), owner VARCHAR(128),
    business_status VARCHAR(32), document_type VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.stg_revisions') IS NULL
CREATE TABLE dbo.stg_revisions (
    revision_id VARCHAR(32), document_id VARCHAR(32), revision_number VARCHAR(16),
    revision_status VARCHAR(32), effective_date VARCHAR(32), end_date VARCHAR(32),
    publication_date VARCHAR(32), channel VARCHAR(32)
);
GO
IF OBJECT_ID('dbo.stg_jobs') IS NULL
CREATE TABLE dbo.stg_jobs (
    job_id VARCHAR(32), revision_id VARCHAR(32), vendor_id VARCHAR(32),
    cost_center_id VARCHAR(32), production_date VARCHAR(32),
    quantity VARCHAR(32), expected_cost VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.stg_vendors') IS NULL
CREATE TABLE dbo.stg_vendors (vendor_id VARCHAR(32), vendor_name VARCHAR(128));
GO
IF OBJECT_ID('dbo.stg_cost_centers') IS NULL
CREATE TABLE dbo.stg_cost_centers (cost_center_id VARCHAR(32), cost_center_name VARCHAR(128));
GO
IF OBJECT_ID('dbo.stg_invoice_lines') IS NULL
CREATE TABLE dbo.stg_invoice_lines (
    source_line_id VARCHAR(32), vendor_id VARCHAR(32), invoice_id VARCHAR(32),
    line_number VARCHAR(16), job_id VARCHAR(32), amount VARCHAR(64), currency VARCHAR(8)
);
GO
IF OBJECT_ID('dbo.dim_document') IS NULL
CREATE TABLE dbo.dim_document (
    document_id VARCHAR(32) NOT NULL, title VARCHAR(256), owner VARCHAR(128),
    business_status VARCHAR(32), document_type VARCHAR(64), snapshot_id VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.dim_revision') IS NULL
CREATE TABLE dbo.dim_revision (
    revision_id VARCHAR(32) NOT NULL, document_id VARCHAR(32) NOT NULL,
    revision_number INT, revision_status VARCHAR(32), effective_date DATE, end_date DATE,
    publication_date DATE, channel VARCHAR(32), snapshot_id VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.dim_vendor') IS NULL
CREATE TABLE dbo.dim_vendor (vendor_id VARCHAR(32) NOT NULL, vendor_name VARCHAR(128));
GO
IF OBJECT_ID('dbo.dim_cost_center') IS NULL
CREATE TABLE dbo.dim_cost_center (cost_center_id VARCHAR(32) NOT NULL, cost_center_name VARCHAR(128));
GO
IF OBJECT_ID('dbo.invoice_disposition') IS NULL
CREATE TABLE dbo.invoice_disposition (
    source_line_id VARCHAR(32) NOT NULL, vendor_id VARCHAR(32), invoice_id VARCHAR(32),
    line_number VARCHAR(16), job_id VARCHAR(32), raw_amount VARCHAR(64),
    parsed_amount DECIMAL(18,2), currency VARCHAR(8), disposition VARCHAR(16),
    reason VARCHAR(64), snapshot_id VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.fact_invoice') IS NULL
CREATE TABLE dbo.fact_invoice (
    source_line_id VARCHAR(32) NOT NULL, vendor_id VARCHAR(32), invoice_id VARCHAR(32),
    line_number VARCHAR(16), job_id VARCHAR(32), amount DECIMAL(18,2),
    disposition VARCHAR(16), snapshot_id VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.fact_job_cost') IS NULL
CREATE TABLE dbo.fact_job_cost (
    job_id VARCHAR(32) NOT NULL, revision_id VARCHAR(32), document_id VARCHAR(32),
    vendor_id VARCHAR(32), cost_center_id VARCHAR(32), production_date DATE,
    channel VARCHAR(32), quantity BIGINT, expected_cost DECIMAL(18,2),
    actual_cost DECIMAL(18,2), variance DECIMAL(18,2), snapshot_id VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.report_catalog') IS NULL
CREATE TABLE dbo.report_catalog (
    document_id VARCHAR(32) NOT NULL, title VARCHAR(256), owner VARCHAR(128),
    business_status VARCHAR(32), document_type VARCHAR(64), current_revision_id VARCHAR(32),
    revision_number INT, channel VARCHAR(32), publication_date DATE, effective_date DATE,
    has_current_publication INT, missing_owner INT, as_of_date DATE, snapshot_id VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.report_reconciliation') IS NULL
CREATE TABLE dbo.report_reconciliation (
    disposition VARCHAR(16), line_count BIGINT, parseable_amount DECIMAL(18,2),
    unparseable_count BIGINT, snapshot_id VARCHAR(64)
);
GO
IF OBJECT_ID('dbo.publication_history') IS NULL
CREATE TABLE dbo.publication_history (
    attempt_id VARCHAR(36), snapshot_id VARCHAR(64), publication_status VARCHAR(16),
    published_at DATETIME2(6), source_line_count BIGINT, message VARCHAR(1024)
);
GO
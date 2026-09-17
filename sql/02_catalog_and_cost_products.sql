CREATE OR ALTER PROCEDURE dbo.publish_document_products
    @snapshot_id VARCHAR(64) = 'DOCUMENT-DEMO-001',
    @as_of_date DATE = '2027-01-01'
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @attempt_id VARCHAR(36) = CONVERT(VARCHAR(36), NEWID());
    BEGIN TRY
        IF (SELECT COUNT_BIG(*) FROM dbo.stg_documents) <> 6
           OR (SELECT COUNT_BIG(*) FROM dbo.stg_revisions) <> 8
           OR (SELECT COUNT_BIG(*) FROM dbo.stg_jobs) <> 7
           OR (SELECT COUNT_BIG(*) FROM dbo.stg_vendors) <> 3
           OR (SELECT COUNT_BIG(*) FROM dbo.stg_cost_centers) <> 3
           OR (SELECT COUNT_BIG(*) FROM dbo.stg_invoice_lines) <> 13
            THROW 51001, 'Incomplete synthetic snapshot. Copy all six sample files before publishing.', 1;

        IF EXISTS (SELECT document_id FROM dbo.stg_documents GROUP BY document_id
                   HAVING COUNT_BIG(*) <> 1 OR NULLIF(document_id, '') IS NULL)
           OR EXISTS (SELECT revision_id FROM dbo.stg_revisions GROUP BY revision_id
                      HAVING COUNT_BIG(*) <> 1 OR NULLIF(revision_id, '') IS NULL)
           OR EXISTS (SELECT job_id FROM dbo.stg_jobs GROUP BY job_id
                      HAVING COUNT_BIG(*) <> 1 OR NULLIF(job_id, '') IS NULL)
           OR EXISTS (SELECT vendor_id FROM dbo.stg_vendors GROUP BY vendor_id
                      HAVING COUNT_BIG(*) <> 1 OR NULLIF(vendor_id, '') IS NULL)
           OR EXISTS (SELECT cost_center_id FROM dbo.stg_cost_centers GROUP BY cost_center_id
                      HAVING COUNT_BIG(*) <> 1 OR NULLIF(cost_center_id, '') IS NULL)
           OR EXISTS (SELECT source_line_id FROM dbo.stg_invoice_lines GROUP BY source_line_id
                      HAVING COUNT_BIG(*) <> 1 OR NULLIF(source_line_id, '') IS NULL)
            THROW 51002, 'Empty or duplicate dimension/source keys block publication.', 1;

        IF EXISTS (
            SELECT 1 FROM dbo.stg_revisions AS revision
            LEFT JOIN dbo.stg_documents AS document ON document.document_id = revision.document_id
            WHERE document.document_id IS NULL
               OR TRY_CONVERT(INT, revision.revision_number) IS NULL
               OR TRY_CONVERT(DATE, revision.effective_date, 23) IS NULL
               OR (NULLIF(revision.end_date, '') IS NOT NULL AND TRY_CONVERT(DATE, revision.end_date, 23) IS NULL)
               OR (NULLIF(revision.publication_date, '') IS NOT NULL AND TRY_CONVERT(DATE, revision.publication_date, 23) IS NULL)
        ) OR EXISTS (
            SELECT 1 FROM dbo.stg_jobs AS job
            LEFT JOIN dbo.stg_revisions AS revision ON revision.revision_id = job.revision_id
            LEFT JOIN dbo.stg_vendors AS vendor ON vendor.vendor_id = job.vendor_id
            LEFT JOIN dbo.stg_cost_centers AS center ON center.cost_center_id = job.cost_center_id
            WHERE revision.revision_id IS NULL OR vendor.vendor_id IS NULL OR center.cost_center_id IS NULL
               OR TRY_CONVERT(BIGINT, job.quantity) IS NULL OR TRY_CONVERT(BIGINT, job.quantity) <= 0
               OR TRY_CONVERT(DECIMAL(18,2), job.expected_cost) IS NULL
               OR TRY_CONVERT(DATE, job.production_date, 23) IS NULL
        )
            THROW 51003, 'Invalid catalog/job references, dates, quantities or costs block publication.', 1;

        BEGIN TRANSACTION;
        DELETE FROM dbo.dim_document;
        DELETE FROM dbo.dim_revision;
        DELETE FROM dbo.dim_vendor;
        DELETE FROM dbo.dim_cost_center;
        DELETE FROM dbo.invoice_disposition;
        DELETE FROM dbo.fact_invoice;
        DELETE FROM dbo.fact_job_cost;
        DELETE FROM dbo.report_catalog;
        DELETE FROM dbo.report_reconciliation;

        INSERT INTO dbo.dim_document
        SELECT document_id, title, NULLIF(owner, ''), business_status, document_type, @snapshot_id
        FROM dbo.stg_documents;
        INSERT INTO dbo.dim_revision
        SELECT revision_id, document_id, CONVERT(INT, revision_number), revision_status,
               CONVERT(DATE, effective_date, 23), CONVERT(DATE, NULLIF(end_date, ''), 23),
               CONVERT(DATE, NULLIF(publication_date, ''), 23), channel, @snapshot_id
        FROM dbo.stg_revisions;
        INSERT INTO dbo.dim_vendor SELECT vendor_id, vendor_name FROM dbo.stg_vendors;
        INSERT INTO dbo.dim_cost_center SELECT cost_center_id, cost_center_name FROM dbo.stg_cost_centers;

        ;WITH ranked AS (
            SELECT source_line_id, vendor_id, invoice_id, line_number, job_id, amount, currency,
                   ROW_NUMBER() OVER (PARTITION BY vendor_id, invoice_id, line_number ORDER BY source_line_id) AS line_rank,
                   CASE WHEN TRY_CONVERT(DECIMAL(28,8), amount) = TRY_CONVERT(DECIMAL(18,2), amount)
                        THEN TRY_CONVERT(DECIMAL(18,2), amount) END AS parsed_amount
            FROM dbo.stg_invoice_lines
        ), classified AS (
            SELECT ranked.*,
                   CASE WHEN line_rank > 1 THEN 'DUPLICATE_LINE'
                        WHEN parsed_amount IS NULL THEN 'INVALID_AMOUNT'
                        WHEN currency <> 'USD' OR currency IS NULL THEN 'UNSUPPORTED_CURRENCY'
                        WHEN job.job_id IS NULL THEN 'UNKNOWN_JOB'
                        WHEN job.vendor_id <> ranked.vendor_id THEN 'VENDOR_MISMATCH'
                        ELSE 'OK' END AS reason
            FROM ranked LEFT JOIN dbo.stg_jobs AS job ON ranked.job_id = job.job_id
        )
        INSERT INTO dbo.invoice_disposition
        SELECT source_line_id, vendor_id, invoice_id, line_number, job_id, amount, parsed_amount, currency,
               CASE WHEN reason = 'OK' THEN 'Matched'
                    WHEN reason IN ('UNKNOWN_JOB', 'VENDOR_MISMATCH') THEN 'Unmatched'
                    ELSE 'Rejected' END,
               reason, @snapshot_id
        FROM classified;

        INSERT INTO dbo.fact_invoice
        SELECT source_line_id, vendor_id, invoice_id, line_number, job_id, parsed_amount, disposition, @snapshot_id
        FROM dbo.invoice_disposition WHERE disposition IN ('Matched', 'Unmatched');

        ;WITH job_amount AS (
            SELECT job_id, SUM(parsed_amount) AS actual_cost
            FROM dbo.invoice_disposition WHERE disposition = 'Matched' GROUP BY job_id
        )
        INSERT INTO dbo.fact_job_cost
        SELECT job.job_id, job.revision_id, revision.document_id, job.vendor_id, job.cost_center_id,
               CONVERT(DATE, job.production_date, 23), revision.channel, CONVERT(BIGINT, job.quantity),
               CONVERT(DECIMAL(18,2), job.expected_cost), COALESCE(job_amount.actual_cost, 0),
               COALESCE(job_amount.actual_cost, 0) - CONVERT(DECIMAL(18,2), job.expected_cost), @snapshot_id
        FROM dbo.stg_jobs AS job
        JOIN dbo.dim_revision AS revision ON revision.revision_id = job.revision_id
        LEFT JOIN job_amount ON job_amount.job_id = job.job_id;

        ;WITH published AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY document_id ORDER BY revision_number DESC, revision_id) AS revision_rank
            FROM dbo.dim_revision
            WHERE publication_date <= @as_of_date AND effective_date <= @as_of_date
              AND (end_date IS NULL OR end_date >= @as_of_date)
              AND revision_status IN ('Published', 'Retired')
        )
        INSERT INTO dbo.report_catalog
        SELECT document.document_id, document.title, document.owner, document.business_status, document.document_type,
               published.revision_id, published.revision_number, published.channel, published.publication_date,
               published.effective_date, CASE WHEN published.revision_id IS NULL THEN 0 ELSE 1 END,
               CASE WHEN document.owner IS NULL THEN 1 ELSE 0 END, @as_of_date, @snapshot_id
        FROM dbo.dim_document AS document
        LEFT JOIN published ON published.document_id = document.document_id AND published.revision_rank = 1;

        INSERT INTO dbo.report_reconciliation
        SELECT disposition, COUNT_BIG(*), SUM(COALESCE(parsed_amount, 0)),
               SUM(CONVERT(BIGINT, CASE WHEN parsed_amount IS NULL THEN 1 ELSE 0 END)), @snapshot_id
        FROM dbo.invoice_disposition GROUP BY disposition;

        IF (SELECT SUM(actual_cost) FROM dbo.fact_job_cost) <>
           (SELECT SUM(parsed_amount) FROM dbo.invoice_disposition WHERE disposition = 'Matched')
            THROW 51004, 'Job-grain costs do not reconcile to matched invoices.', 1;
        INSERT INTO dbo.publication_history
        VALUES (@attempt_id, @snapshot_id, 'Succeeded', SYSUTCDATETIME(),
                (SELECT COUNT_BIG(*) FROM dbo.stg_invoice_lines), 'Atomic synthetic snapshot publication');
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        INSERT INTO dbo.publication_history
        VALUES (@attempt_id, @snapshot_id, 'Failed', SYSUTCDATETIME(),
                (SELECT COUNT_BIG(*) FROM dbo.stg_invoice_lines), LEFT(ERROR_MESSAGE(), 1024));
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER VIEW dbo.v_catalog_history AS
SELECT document.document_id, document.title, document.owner, document.business_status,
       revision.revision_id, revision.revision_number, revision.revision_status, revision.channel,
       revision.publication_date, revision.effective_date, revision.end_date, revision.snapshot_id
FROM dbo.dim_document AS document
JOIN dbo.dim_revision AS revision ON revision.document_id = document.document_id;
GO
CREATE OR ALTER VIEW dbo.v_current_catalog AS
SELECT * FROM dbo.report_catalog WHERE has_current_publication = 1;
GO
CREATE OR ALTER VIEW dbo.v_cost_reconciliation AS
SELECT * FROM dbo.invoice_disposition WHERE disposition <> 'Matched';
GO
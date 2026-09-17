# Requirements Traceability | Document Administration

This original synthetic workshop demonstrates a reusable document catalog and financial reporting pattern. `DA-*` IDs identify learning requirements. **Built** means a synthetic implementation; **Context/gate** means described, not connected or certified. No organization's system inventory, business targets, or source documents are included.

| ID | Learning Requirement and Coverage | Learner Module | Artifact | Acceptance |
| --- | --- | --- | --- | --- |
| DA-01 | Connect document ownership, publication history, production accountability, and financial analysis. Context/gate. | [Start](../lab-guide/00-start.md) | [Runbook](../instructor/README.md) | Distinguish an illustrative scenario, future integration, and synthetic results. No achieved-savings claim. |
| DA-02 | Catalog/mastering: item and revision identity, owners, status, relationships, publication, physical/digital inventory and lifecycle precede cost reconciliation. Built subset. | [Products](../lab-guide/03-products.md) | [Publication SQL](../sql/02_catalog_and_cost_products.sql) | [SQL checks](../sql/03_validate.sql): 6 items, 8 revisions, 4 current, missing owner, retained history; catalog node. |
| DA-03 | Separate reusable acquisition, transformation, and publication while preserving operational workflows. Built synthetic pattern; enterprise sources are context. | [Ingestion](../lab-guide/02-ingestion.md) | [Pipeline builder](../solution/build_pipeline.py) | Six sequential copies, atomic products, no Spark; current source boundary and proposed product layers. |
| DA-04 | Shared financial reporting, production cost, variance and vendor oversight, without invoice join fan-out. Built subset. | [Products](../lab-guide/03-products.md) | [Dictionary](data-dictionary.md) | $11,305 = $8,725 + $480 + $2,100; 1 unparseable; 10,600 units; cost/reconciliation nodes. |
| DA-05 | Publish reusable semantic definitions and an analyst-facing report. Built model/report templates; deployed rendering and access require separate checks. | [Report](../lab-guide/04-report.md) | [Model reference](../solution/portable/measures.md) | Validate 16 DAX measures, three pages, displayed cards, and filter/reset with the [runbook](../instructor/README.md); optional Excel; reporting node. |
| DA-06 | Preserve all seven document subject areas, including lifecycle and archival reporting. Context/gate beyond catalog/cost subset. | [Wrap-up](../lab-guide/06-wrap-up.md) | [Seven-subject coverage below](#seven-subject-coverage) | All seven are documented below; no full subject-area implementation claim. |
| DA-07 | Governance, ownership, audit, source history, recovery, refresh, and integration ownership. Built synthetic audit/recovery; production governance is a gate. | [Validate](../lab-guide/05-validate.md) | [Runbook](../instructor/README.md) | Check replay and failed-publication preservation in your environment; governance/detail panels. |
| DA-08 | Distinguish analytical integration from replacement of operational workflows. Context/gate. | [Wrap-up](../lab-guide/06-wrap-up.md) | [Runbook](../instructor/README.md) | Generic operational, content, contract, composition, archive, fulfillment, publishing, and financial system categories; source boundary and ownership gates. |

## Seven-Subject Coverage

| Subject | What the Lab Does | Production Follow-up |
| --- | --- | --- |
| Catalog/mastering and physical/digital inventory | Items, revisions, owners, statuses, channels, publication/current history | Enterprise identity, relationships, mastering contracts and inventory completeness |
| Communication preferences and constraints | Architectural context only | Consent, restrictions, precedence, jurisdiction and enforceable policy |
| Constituents | Architectural context only | Approved identity, relationships, privacy and source reconciliation |
| Access and delivery history | Architectural context only | Event definitions, secure capture, recipient evidence and retention |
| Cost and financial reporting | Jobs, vendor/center dimensions, invoices, credits, exceptions and variance | Finance-approved allocation, contractual pricing and vendor reconciliation |
| Operational/process/audit/regulatory/mandate/vendor reporting | Publication audit and synthetic exception review; broader subject in context | Preserve SSRS operations; mandate evidence, vendor SLA and accountability |
| Lifecycle and archival reporting | Retired/archived/future/current revisions retained and queryable | Retention/legal hold, disposal approval, archive completeness and EDW partnership |

## Evidence Boundaries

Read the [runbook](../instructor/README.md) before creating deployment bindings. Generate SQL/model/replay evidence separately from authenticated report-browser evidence. Neither replaces a deployment rehearsal, individual-license check, non-owner access test, capacity assessment, or privacy review.
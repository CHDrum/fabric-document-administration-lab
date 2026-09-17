# Validation Status | Document Administration

This is a portable synthetic lab, not a hosted deployment. Example bindings are placeholders. No private tenant inventory, deployment evidence, run history, or report capture is distributed. Local tests and offline document checks do not prove a cloud deployment or audience access.

## Local Checks

Run `python -m pytest tests -q -p no:cacheprovider` from the repository root. The suite checks deterministic input/results, pipeline ordering, model/report definitions, request rebinding, and guide navigation. The repository's validation workflow repeats the local suite without cloud credentials.

## Your Deployment

| Check | Required Result |
| --- | --- |
| Complete pipeline | All six Copies and publication Script succeed |
| Warehouse acceptance | All 22 assertions in [SQL validation](../sql/03_validate.sql) return no failures |
| Explicit model | All 16 measures match, including $8,725 spend, $0.8231 unit cost, and $436.25 illustrative scenario |
| Replay | Published catalog/revisions/jobs/dispositions/reconciliation remain unchanged |
| Failed publication | Invalid synthetic quantity is rejected; previous products preserved; staging restored; failed audit retained |
| Browser report | All three pages and twelve cards render correctly; document filters and reset work |
| Audience access | Approved non-owner can perform only intended actions with an eligible license |
| Readiness | Capacity, learner access, workspace isolation, timing, and recovery rehearsed locally |

Follow the [runbook](../instructor/README.md). Save actual bindings, exports, and verification evidence only in ignored local folders. Do not replace placeholder packages with tenant-bound requests before distributing the repository.

## Production Gates

Production connectivity, complete domain coverage, privacy/access/export/retention controls, financial approval, realistic capacity sizing, and an atomic cross-run lock are not supplied. Shared staging has no cross-run lease; serialize runs. Assess current dependency advisories before use. No synthetic variance or scenario proves achieved savings or regulatory compliance. Delete only an explicitly approved disposable workspace; never shared capacity.
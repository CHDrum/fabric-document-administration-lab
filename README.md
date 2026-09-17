# Document Administration in Microsoft Fabric

A synthetic workshop for building reusable document catalog and cost/financial data products. Preserve existing operational workflows while separating analytical acquisition, transformation, and publication from report-specific procedures.

**Audience:** Fabric beginners, working in pairs or individually. **Hands-on time:** 130 minutes. **Learner tools:** browser and the repository ZIP. No local Python, Git, CLI, or Power BI Desktop is required.

## Start Here

1. Select **Code > Download ZIP** and extract it. Sign in to GitHub first if repository access requires it.
2. Complete the [lab guide](lab-guide/README.md) in **your organization's tenant** and assigned capacity. Provision your own lab workspace; no shared demo access is included.
3. Use the [instructor runbook](instructor/README.md) for deployment preparation and the [validation checklist](docs/validation-status.md) to verify your own environment.

## What You Build

`Six synthetic CSVs -> DocumentLanding Files -> DocumentIngestion -> DocumentProducts Warehouse -> DocumentAnalytics -> Power BI`

There is no Spark dependency in this lab. Uploading to Lakehouse **Files** does not create Delta **Tables**. The semantic model is created explicitly over physical Warehouse products; it is not an automatically supplied default model.

| Verified reference result | Value |
| --- | ---: |
| Documents / revisions / jobs | 6 / 8 / 7 |
| Current publications at 2027-01-01 | 4 |
| Produced units | 10,600 |
| Expected / matched actual job cost | $8,450.00 / $8,725.00 |
| Cost variance | $275.00 |
| Parseable source amount | $11,305.00 |
| Unmatched / rejected parseable amount | $480.00 / $2,100.00 |
| Unparseable invoice lines | 1 |

All dollars are synthetic USD. A 5% teaching scenario equals $436.25; it is not a forecast or achieved savings.

## Deployment Status

This repository contains a portable lab, not access to a hosted service. Supply your own workspace, capacity, identities, and bindings. See the [validation status and remaining gates](docs/validation-status.md).

After deployment, validate the pipeline, 22 SQL assertions, all 16 model measures, replay, failure preservation, and authenticated report rendering in your own environment. **User access requires appropriate permissions and eligible licenses.** Reference results do not guarantee availability or capacity for your workshop.

## Repository Contents

| Location | Purpose |
| --- | --- |
| [lab-guide](lab-guide/README.md) | Seven portal-first modules, checkpoints, challenges, and answers |
| [data/sample](data/sample) | Six fabricated input tables and the expected result contract |
| [sql](sql) | Schema, publication procedure, views, and live acceptance checks |
| [solution](solution) | Rebindable pipeline, model, and original report builders |
| [portable measure reference](solution/portable/measures.md) | Exact table aliases, DAX, formats, and relationships |
| [instructor runbook](instructor/README.md) | Deployment, binding, replay, recovery, workshop delivery, and handoff |
| [data dictionary](docs/data-dictionary.md) | Source fields, product grains, current-publication and financial semantics |
| [requirements traceability](docs/requirements-traceability.md) | DA-01 through DA-08 and all seven document subjects |
| [tests](tests) | Data, request, model, report, helper, and guide checks |

The complete 5.5-hour workshop combines 20 minutes of orientation, this 130-minute lab, a 20-minute break, a companion 130-minute enrollment-file analysis lab, and 30 minutes of wrap-up. Reserve an optional 30-minute buffer.

## Boundaries

No production documents, customer records, credentials, source connections, compliance certification, or achieved-savings claims. Enterprise systems are generic context, not live integrations. Use one active pipeline per lab workspace. Do not pause or delete shared capacity as cleanup. Do not expose tenant data or reports through Publish to web.

Original teaching material; the [FabricHackathon lab guide](https://github.com/nairsanjeev/FabricHackathon/tree/master/lab-guide) informed sequencing and navigation only.
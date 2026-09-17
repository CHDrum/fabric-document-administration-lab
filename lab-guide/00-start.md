# 00 - Start and Scope

**Duration:** 10 minutes

**Objective:** establish the correct learner environment and distinguish an analytical data product from an operational replacement.

## Steps

1. Sign in to [Fabric](https://app.fabric.microsoft.com/) with your organizational work account. Verify the tenant in the account menu. Do not use the instructor's testing tenant as your build destination.
2. Confirm with the facilitator that your tenant permits Fabric, Warehouse, Data Factory pipelines, and Power BI web modeling. If a control is unavailable, stop at that prerequisite; do not substitute a production workspace.
3. Use **Workspaces > New workspace**. Name it `Fabric-DA-<your-pair-name>`. In workspace settings, assign the administrator-approved Fabric capacity or an eligible, administrator-permitted Fabric trial. Do not purchase capacity or change an organization's shared settings to unblock a lab.
4. Confirm you can create items in the workspace. The learner author needs an appropriate workspace role, such as Contributor in this isolated lab, plus required item permissions. Creation/assignment of workspaces can require separate permissions. Capacity assignment is not an individual Power BI license; verify authoring and below-F64 viewing requirements independently.
5. Sign in to GitHub, open this private repository, select **Code > Download ZIP**, and extract it. Keep the repository folder open alongside the Fabric portal. No terminal is needed for the learner path.
6. Review the [learning requirements](../docs/requirements-traceability.md). Compare the implemented catalog/cost subset with the broader document domain, and explain why operational workflows remain in place.

## Business Checkpoint

This illustrative scenario connects document ownership, publication history, production accountability, and financial analysis. Item/revision catalog quality supports trustworthy cost reconciliation. All records and amounts are synthetic; no scenario value represents a business target, forecast, or achieved savings.

## Completion Checklist

- [ ] Correct your tenant and isolated workspace; capacity and licenses confirmed.
- [ ] Authenticated ZIP available; only synthetic artifacts will be uploaded.
- [ ] One named operator per pair will run the pipeline; no parallel manual or scheduled runs.
- [ ] You can explain what the lab does not replace.

## Challenge and Answer

**Question:** Why not migrate every SSRS report immediately?

**Answer:** Some reports support operational workflows, not only analytics. Discover those dependencies first. Reusable acquisition and publication reduce duplicated report-specific logic without breaking the operational process.

## Recovery

Missing Fabric features usually indicate tenant, capacity, permission, or license prerequisites. Ask the facilitator to resolve that specific gate. Do not create an anonymous repository link, use another person's login, or move data into a personal tenant.

[Guide](README.md) | [Next: Land the snapshot](01-landing.md)
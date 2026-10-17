# WIZ GitHub Mode Hemat — Website SOP

Status: shared baseline for all WIZ website repositories. Apply alongside each site's editorial, SEO, security, AdSense and publication gates. This SOP does not override stricter release gates.

## Principle
**Complete corrections as one coherent batch before invoking GitHub Actions.** Small requests, typo fixes, layout tweaks, repeated prompts and intermediate edits must not each trigger expensive CI, crawls, audits, or deploys.

## Workflow
1. **Audit first:** inspect current main/PR, live website, templates, dependencies and existing checks. Record defects and evidence.
2. **Collect findings:** group related fixes into a single scoped batch/branch; avoid unnecessary global CSS/template changes and duplicate work.
3. **Fix locally/in branch:** apply all changes; use static inspection and targeted checks that do not consume GitHub Actions minutes. Commit as needed without heavy CI.
4. **Batch QC:** verify links, anchors, canonical, metadata, sitemap, structured data, responsive behavior, accessibility, content quality and relevant site-specific gates.
5. **One final validation:** when the batch is stable, run lightweight essential CI once. Run deep audits, Playwright/full regression, bulk builds, crawling, backfills and migrations only manually/on-demand when necessary, ideally once at the end.
6. **If validation fails:** group corrections and use local/light checks; rerun expensive validation once after the correction batch, not for every tiny change.
7. **Release gate:** merge/publish only when required checks are GREEN and review gates CLEAR & CLEAN; then verify actual production and log evidence. Do not equate a merged PR with confirmed deployment.

## Workflow policy
- Prefer `workflow_dispatch` for costly validation on feature branches; avoid `pull_request` triggers for heavy jobs.
- Keep a minimal, reliable safeguard on `main` and any security-critical checks required by branch protection.
- Apply `paths` / `paths-ignore` carefully; changes to shared layouts, routing, SEO tooling, workflows or configuration must still receive the relevant validation.
- Use `concurrency` with `cancel-in-progress` for superseded non-production PR checks; do not cancel critical deployment/migration jobs without a safety design.
- Set least-privilege `permissions`, reasonable `timeout-minutes`, and avoid unnecessary matrix jobs, duplicate schedules, artifact uploads and repeated dependency installation.
- Do not disable required status checks without first aligning branch protection and the replacement manual approval/check mechanism.
- Production, database migrations, credentials and destructive changes require separate explicit safeguards; no automatic merge/deploy from a passing lightweight check alone.

## Per-batch record
Record: scope and changed files; audit findings; checks run and their results; one final Actions run URL (if applicable); PR/merge SHA; production verification; open risks.

## Short rule
**Audit → collect findings → fix in batch → local QC → one final Actions validation → release gate → merge/publish → production verification.**

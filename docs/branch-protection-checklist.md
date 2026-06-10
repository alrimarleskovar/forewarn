# Branch Protection & Settings — Checklist (manual, post-push)

Apply in the repo settings on GitHub after the first push. Everything here is repo settings — it does not go in a workflow.

## Branch protection on `main`

`Settings → Branches → Add branch protection rule` (pattern: `main`):

- [ ] **Require a pull request before merging** — with **1 approving review**.
- [ ] **Require status checks to pass before merging**, including:
  - [ ] CI: `quant`, `ingestion`, and **`preregistration-gate`**
  - [ ] CodeQL (`javascript-typescript` and `python`)
- [ ] **Require branches to be up to date before merging** (recommended).
- [ ] **Do not allow force pushes** on `main`.
- [ ] **Do not allow deletions** (recommended).

## Automated security

`Settings → Code security and analysis`:

- [ ] **Secret scanning** enabled.
- [ ] **Push protection** (from secret scanning) enabled.
- [ ] **Dependabot alerts** enabled.
- [ ] **Dependabot security updates** (recommended).
- [ ] **CodeQL**: confirm that the `codeql.yml` workflow appears and runs (default setup OFF — we use advanced via workflow).

## Afterwards

- [ ] Verify that the pre-registration commit appears in the timeline **before** any content in `dune/queries/`.

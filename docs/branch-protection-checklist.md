# Branch Protection & Settings — Checklist (manual, pós-push)

Aplicar nas settings do repo no GitHub após o primeiro push. Tudo aqui é settings de repo — não vai em workflow.

## Branch protection em `main`

`Settings → Branches → Add branch protection rule` (pattern: `main`):

- [ ] **Require a pull request before merging** — com **1 approving review**.
- [ ] **Require status checks to pass before merging**, incluindo:
  - [ ] CI: `quant`, `ingestion` e **`preregistration-gate`**
  - [ ] CodeQL (`javascript-typescript` e `python`)
- [ ] **Require branches to be up to date before merging** (recomendado).
- [ ] **Do not allow force pushes** em `main`.
- [ ] **Do not allow deletions** (recomendado).

## Segurança automática

`Settings → Code security and analysis`:

- [ ] **Secret scanning** habilitado.
- [ ] **Push protection** (de secret scanning) habilitado.
- [ ] **Dependabot alerts** habilitado.
- [ ] **Dependabot security updates** (recomendado).
- [ ] **CodeQL**: confirmar que o workflow `codeql.yml` aparece e roda (default setup OFF — usamos advanced via workflow).

## Depois

- [ ] `gh auth login` e rodar `scripts/seed-issues.sh` (milestones + issues).
- [ ] Conferir que o commit do pré-registro aparece na timeline **antes** de qualquer conteúdo em `dune/queries/`.

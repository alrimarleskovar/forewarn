# dune/

The project's Dune queries (**MIT** license).

## ⚠️ This folder is intentionally empty

**No `.sql` file here may receive content until the commit of `docs/validation-preregistration.md` — with the thresholds table (§ 4) filled in — has been committed and pushed to the remote** (GUARDRAIL 4 / Gate Zero; see `CONTRIBUTING.md`).

The `preregistration-gate` job in CI fails if there is a non-empty `.sql` file here while § 4 of the pre-registration still contains `[___]`.

Once unblocked, every query must reference the **hash of the pre-registration commit** in its header.

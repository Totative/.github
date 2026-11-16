# AGENTS.md

Org defaults for Totative, a software security research group: the public profile, the community health files, and the reusable source-release workflow other Totative repos call. `profile/README.md` is the org page at github.com/Totative; there is no root README.

## Layout

- `profile/README.md` and `profile/assets/`: the profile, wordmark and mark (light and dark), the avatar, and social cards for each repo.
- `SECURITY.md`: how to report to Totative. `DISCLOSURE.md`: how Totative reports bugs in software it does not own (private report, 14 days to hear back or hand to CERT/CC, publish at 90 days or 30 days after a fix). `CONTRIBUTING.md`: default for repos without their own.
- `.github/workflows/release-source.yml`: reusable (`workflow_call`) release build for SLSA v1 Build Level 3. It runs `git archive`, makes an SBOM, attests, and publishes; callers pin it by commit SHA. `codeql.yml`, `dependency-review.yml`, `scorecard.yml`, `.github/dependabot.yml`, `ISSUE_TEMPLATE/`.
- `lefthook.yml` and `.gitleaks.toml`: the canonical copies every Totative repo commits as they are.

## Gate

`gate` runs gitleaks (skipped in CI) from `.gate.toml`. Lint Markdown with `bunx --bun markdownlint-cli2 '**/*.md'`; `.markdownlint-cli2.jsonc` allows the few HTML elements the profile needs.

## Invariants

- Changing `release-source.yml` changes the signer of every release's provenance. Callers pin a SHA, so update `repo-template` and each caller's pin in follow-up commits.
- Do not edit `lefthook.yml` or `.gitleaks.toml` here without propagating to every Totative repo.
- The profile tagline and the "What we do" cards are duplicated in `totative.github.io`; `scripts/check-copy.py` there fails CI if they differ. Change both together.
- Public repo: no unreleased research, no names of targets under embargo.
- Actions are pinned to a full commit SHA.

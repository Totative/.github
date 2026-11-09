# Contributing

Applies to every Totative repository without its own `CONTRIBUTING.md`.

- Security problems go through the [security policy](https://github.com/Totative/.github/blob/main/SECURITY.md), never an issue or pull request.
- Sign every commit; public repositories reject unsigned ones. Set up [SSH commit signing](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key) before you open a pull request.
- One change per pull request, with the reason in the description. Required checks pass and a maintainer reviews before merge.
- A new dependency needs a reason in the pull request. Dependency review blocks known-vulnerable packages and disallowed licences.
- Workflows pin third-party actions to a full commit SHA and set least-privilege `permissions:` per job.

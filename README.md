# .github

Organization defaults for [Totative](https://github.com/Totative). The org profile is [`profile/README.md`](profile/README.md); this file describes the repo.

- [`SECURITY.md`](SECURITY.md): how to report a vulnerability to us.
- [`DISCLOSURE.md`](DISCLOSURE.md): how we report vulnerabilities in software we don't maintain.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): the default for repos without their own.
- `.github/workflows/release-source.yml`: a reusable workflow that builds, attests and publishes a source release, so other Totative repos get SLSA Build L3 provenance. Verify a release with `gh attestation verify ARCHIVE --owner Totative --signer-workflow Totative/.github/.github/workflows/release-source.yml`.
- `lefthook.yml` and `.gitleaks.toml`: the secret-scanning hook every Totative repo copies as it is.

Apache-2.0, see [LICENSE](LICENSE).

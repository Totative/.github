# Security policy

Covers every repository under [github.com/Totative](https://github.com/Totative) and everything released from them.

## Reporting

Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability): the affected repository's **Security** tab, then **Report a vulnerability**. Don't use an issue, pull request or discussion.

Include:

- the repository, and the affected version, release or commit;
- what an attacker gets, and under which conditions;
- steps to reproduce, or a proof of concept;
- whether anyone else knows about it.

## What happens next

We work the report inside its private advisory, so you see each status change and can comment on the fix.

The advisory goes public when the fix ships, or 90 days after your report, whichever comes first. If a fix is close, either of us can ask for more time in the advisory thread.

Confirmed vulnerabilities get a CVE through GitHub (a CVE Numbering Authority). You're credited in the advisory unless you'd rather not be.

## Safe harbour

If you research in good faith and follow this policy, we treat your research as authorized. We won't pursue or support legal action against you over it, including under anti-hacking laws or our terms. If someone else takes action against you over research that followed this policy, we'll say publicly that it was authorized.

Good faith means you avoid privacy violations, destroying data and disrupting services; you only access what you need to show the problem; and you keep the details private until the advisory is published.

## Verifying releases

Every release artifact carries signed build provenance and an SBOM attestation:

```sh
gh attestation verify <file> --owner Totative
```

If verification fails, or there's no attestation, report that too.

# Disclosure policy

How we report vulnerabilities we find in software we don't maintain. For reporting a vulnerability to us, see the [security policy](SECURITY.md).

## Reporting

We report privately to the maintainer, through the channel they publish: a `security.txt`, a `SECURITY.md`, or GitHub's private vulnerability reporting. If there isn't one, we ask for a private contact first. If no maintainer answers within 14 days, we hand the report to [CERT/CC](https://www.kb.cert.org/vince/).

The report includes the affected versions, what an attacker gets, steps to reproduce, and the date we plan to publish.

## Deadlines

We publish 90 days after our report, or 30 days after the fix ships if that comes first, so users have time to update. If the maintainer tells us a fix will ship within 14 days after the deadline, we wait for it.

A vulnerability that is already being exploited gets 7 days.

## What we publish

A write-up with the affected and fixed versions, the timeline, and enough detail to check our work, proof of concept included. The maintainer sees it before it goes out. We ask for a CVE through the project's CVE Numbering Authority, or through GitHub's if the project has none.

## What we won't do

- Test against systems we don't own. We run our own copies of the software.
- Share a finding before publication with anyone except the maintainer and a coordinator.
- Sell findings, or make a report depend on payment.

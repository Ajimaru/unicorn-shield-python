# Security Policy

## Supported Versions

Only the `master` branch is supported. This is a hobby project — there are no
released versions and no backports.

## Reporting a Vulnerability

Report privately via
[GitHub Security Advisories](https://github.com/Ajimaru/unicorn-shield-python/security/advisories/new),
not through a public issue.

Expect a first reply within about two weeks. If a report is accepted, the fix
lands on `master`; if it is declined, you get the reasoning.

## Scope

The HTTP API in `coding-unicorn-shield-projects/http-api/` has **no
authentication** and controls hardware directly. It is meant to bind
`127.0.0.1` and be reached only by a local frontend. Exposing it to a network
is a deployment mistake, not a vulnerability in this repository.

Dependencies are pinned to the last releases supporting Python 3.7, which the
target hardware runs — see [README.md](README.md#dependencies-and-dependabot).
Advisories against newer versions that cannot be installed there are expected
and are dismissed with that reasoning.

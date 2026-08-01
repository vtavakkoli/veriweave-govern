# Security policy

## Supported versions

VeriWeave Govern is under active development. Security fixes are provided for
the latest minor release line only.

| Version | Supported |
|---|---|
| 0.2.x | Yes |
| 0.1.x and earlier | No |

## Reporting a vulnerability

Do **not** open a public issue for a suspected vulnerability.

Use GitHub's private vulnerability-reporting flow under the repository's
**Security** tab when available. Otherwise, email `vahid.tavakkoli@aau.at` with
the subject `VeriWeave Govern security report`.

Include, where possible:

- the affected version or commit;
- deployment assumptions and configuration;
- reproduction steps or a minimal proof of concept;
- expected and observed behavior;
- impact and realistic attack prerequisites;
- suggested remediation, if known.

Please avoid accessing data that is not yours, disrupting services, or
publishing details before a fix and disclosure plan are agreed.

## Response process

The maintainer will aim to:

1. acknowledge a complete report within five business days;
2. validate severity and affected versions;
3. coordinate remediation and release timing;
4. credit the reporter when requested and appropriate;
5. publish an advisory after users have a reasonable opportunity to update.

These targets are best-effort and do not create a service-level agreement.

## Security boundary

The current MVP does not provide a complete production security boundary. In
particular, production deployments require external controls for identity,
authorization, tenant isolation, durable storage, secret management, network
security, rate limiting, monitoring, backup, key rotation, policy approval,
and incident response.

The example HMAC signing key, development configuration, and Docker Compose
settings must not be used unchanged in production.

## Supply-chain expectations

- Pin and review dependencies before a production release.
- Build images in a trusted CI environment.
- Retain software bills of materials and image digests.
- Scan containers and Python dependencies.
- Protect signing keys with a managed secret store or hardware-backed service.
- Review policy changes with separation of duties.

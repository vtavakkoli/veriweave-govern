# Sanitized reference case studies

These are reference architectures, not claims that deployments have occurred.

## Enterprise copilot/tool agent

Govern document search, summarization, external email, ERP/API writes and classified information. Low-risk reads may proceed with required evidence; restricted external release is denied; high-impact actions route to accountable review.

## Software-engineering agent

Example ladder: repository read → allow; branch creation → allow/review; protected merge → review; production deployment → review with change/rollback evidence; destructive production action or secret exfiltration → deny. Test tool substitution, action decomposition, unregistered delegation and policy-version downgrade.

## Public-administration assistant

Govern citizen-data access, automated recommendations, sensitive-data release, human oversight, action logging, policy provenance and evidence retention. Any regulatory mapping must be validated for the specific procedure/jurisdiction; VeriWeave supplies technical enforcement/evidence, not a legal determination.

For pilots capture request/action inventory, policy version, evidence, reviewer ownership, decision, counterfactuals, audit-chain reference, latency, and observed false allow/review/deny.

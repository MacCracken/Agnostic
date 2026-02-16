# Security

## Vulnerability Reporting

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email the maintainers at qa@example.com with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
3. Allow up to 72 hours for an initial response

## Security Assessment

For the full security assessment report, findings, and remediation status, see:

**[Security Assessment Report](security/assessment.md)**

This includes:
- Critical, high, and medium priority findings
- Implementation status of remediations
- Risk assessment and compliance considerations
- Security best practices implemented

## Security Best Practices

- Never commit secrets or API keys
- Use environment variables for all credentials (see `.env.example`)
- Run `bandit -r agents/ config/ shared/` before submitting PRs
- Follow OWASP security guidelines for any web-facing changes

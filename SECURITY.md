# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Yes    |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing **darshjme@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

You will receive a response within 72 hours.  
If confirmed, a patch will be released within 14 days and you will be credited.

## Scope

agent-saga is a pure-Python library with zero runtime dependencies.
The primary attack surface is **user-supplied callables** passed as `action`
and `compensate` arguments — these execute with the caller's process permissions.
Validate and sandbox untrusted callables before registering them as saga steps.

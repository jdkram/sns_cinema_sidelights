`#ai-input`

# Security and disclosure policy

## Access control

- Do not publish device login credentials in this repository.
- Do not publish private network names, PSKs, or direct host addressing details.
- Operational credentials should be shared directly with authorised cinema maintainers.

## Sensitive data classes

Treat these as non-public:

- passwords, private keys, tokens
- shell history from production systems
- full filesystem dumps from deployed devices
- internal-only infrastructure and location details beyond what is needed for maintenance

## Incident response

If sensitive information is accidentally pushed:

1. rotate exposed credentials immediately
2. remove data from current branch
3. rewrite git history before republishing
4. notify maintainers of exposure window

## Reporting

For operational/security issues, contact the current Star and Shadow technical maintainers directly.

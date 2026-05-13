# Security Policy

SafeLens is research infrastructure for inspecting and adapting LLM safety
signals. Security issues can affect users through dependency vulnerabilities,
unsafe model loading, accidental credential exposure, or unsafe handling of
private datasets.

## Supported Versions

The `main` branch is the actively maintained development version until tagged
releases are introduced.

| Version | Supported |
| --- | --- |
| `main` | Yes |
| Older snapshots | No |

## Reporting a Vulnerability

Please do not publicly disclose vulnerabilities before maintainers have had a
reasonable chance to investigate.

Preferred reporting paths:

1. Use GitHub private vulnerability reporting if it is enabled for this
   repository.
2. Otherwise, contact the repository maintainers through the PKU-PILLAR-Group
   organization or project coordination channel.

Include:

- A concise description of the issue.
- Steps to reproduce.
- Impact and affected versions or commits.
- Whether credentials, private data, model files, or remote code execution are
  involved.

## Security Expectations

- Do not commit API keys, tokens, private prompts, private datasets, model
  weights, or generated safety reports containing sensitive data.
- Avoid enabling `trust_remote_code` unless the model source is trusted and the
  code has been reviewed.
- Keep network-dependent tests out of the default CI path.
- Prefer explicit allowlists for model adapters, hook names, and report
  conversion targets.

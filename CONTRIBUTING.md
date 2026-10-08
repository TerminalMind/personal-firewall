# Contributing to Personal Guard

Thank you for your interest in contributing! Bug fixes, documentation improvements, tests, and feature suggestions are welcome.

## Getting Started

1. Fork this repository and clone your fork.
2. Open a terminal in the project folder.
3. Create a branch:

```bash
git switch -c feature/your-feature-name
```

### Requirements

- Python 3.9 or newer.
- Linux and nftables for actual firewall operations.
- Administrator privileges to apply or remove rules.

Install dependencies on Kali or Ubuntu:

```bash
sudo apt update
sudo apt install python3 nftables
```

No additional pip packages are required.

## Making Changes

- Keep each contribution focused on one issue or feature.
- Write readable Python with clear names and four-space indentation.
- Prefer the Python standard library.
- Explain any new dependencies.
- Update documentation when commands or behavior change.
- Add focused tests for bug fixes and behavior changes.

### Firewall Guidelines

- Validate configuration before applying rules.
- Preserve preview-by-default behavior.
- Require `--commit` for permanent application or removal.
- Modify only the project's owned `inet personal_guard` table.
- Never flush the entire system ruleset.
- Preserve ownership checks, atomic updates, and mutation locking.
- Do not pass untrusted input to a shell.
- Explain changes to rule order and connection handling.
- Consider IPv4 and IPv6 behavior.

## Testing

Run unit tests from the project folder:

```bash
python3 -m unittest discover -s tests -v
```

Preview the generated rules:

```bash
python3 firewall.py preview rules.json
```

Validate rules against the Linux kernel without installing them:

```bash
sudo python3 firewall.py check rules.json
```

Unit tests should mock privileged operations. Passing unit tests does not prove live packet filtering works.

### Live Testing

Use a disposable Linux VM or an isolated lab with local console access. The default rules block new incoming SSH connections.

Run a temporary trial:

```bash
sudo python3 firewall.py trial rules.json --seconds 30
```

The trial normally restores the previous configuration when the timer finishes or Ctrl+C is handled. It is a foreground process: terminal closure, forced termination, or system failure can prevent restoration.

For filtering tests:

1. Confirm connectivity before applying a blocking rule.
2. Apply the rule and repeat the connection attempt.
3. Verify that the matching drop counter increases.
4. Remove the rule and confirm connectivity returns.

A timeout alone does not prove blocking. Testing through localhost does not verify incoming filtering from another VM because loopback traffic is accepted.

Remove the project's rules with:

```bash
sudo python3 firewall.py disable --commit
```

Do not remove unrelated firewall rules or disable other security tools.

## Reporting Bugs

Open an issue containing:

- A clear description of the problem.
- Your Linux distribution, Python version, and nftables version.
- Steps and commands to reproduce the issue.
- Expected behavior and actual behavior.
- Relevant error messages.
- A minimal configuration with private information removed.

Mention other firewall managers if they may affect the result.

## Reporting Security Vulnerabilities

Do not publish exploitable vulnerability details in public issues or pull requests.

Follow `SECURITY.md` if available. Otherwise, use GitHub's private vulnerability reporting option if enabled.

If no private reporting method exists, ask the maintainer to establish one without sharing vulnerability details publicly.

## Suggesting Features

For substantial changes, open an issue first and explain:

- The problem the feature solves.
- The proposed behavior.
- Any additional dependencies or privileges.
- Effects on existing rules and compatibility.

Keep suggestions aligned with a simple, readable firewall for learning and controlled lab use.

## Submitting a Pull Request

1. Make changes on a separate branch.
2. Run the relevant tests.
3. Review your changes.
4. Commit with a descriptive message.
5. Push your branch.
6. Open a pull request against the repository's default branch.

Include the following in your pull request:

### Problem

Explain what needs fixing or improving.

### Changes

Describe what changed and how it affects users.

### Verification

List the tests or commands you ran and their results.

### Limitations

Mention anything untested or requiring further attention.

Link the related issue if applicable. Do not claim live filtering was verified when only unit tests were run.

## Files and Screenshots

Do not commit:

- `__pycache__` folders or `.pyc` files.
- Virtual environments.
- Passwords, tokens, or other secrets.
- Generated ZIP archives.
- Sensitive logs or packet captures.

Use descriptive screenshot filenames and relative Markdown links. Review screenshots for private information before uploading.

## Community Guidelines

- Be respectful and welcoming.
- Give constructive feedback.
- Explain technical disagreements clearly.
- Support contributors who are learning.
- Only contribute code and assets you have permission to share.

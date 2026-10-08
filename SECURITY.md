# Security Policy

## Project Scope

Personal Guard is a Python personal firewall for Linux that uses nftables to filter incoming and outgoing traffic.

This is an educational and portfolio project. It is not a replacement for a maintained production security solution, antivirus software, or an intrusion detection system.

## Supported Code

Security fixes target the latest code on the repository's default branch. Older commits and modified copies are not maintained separately.

No guaranteed response time or security support period is provided.

## Reporting a Vulnerability

Please do not disclose exploitable vulnerabilities in public issues or pull requests.

If private vulnerability reporting is enabled:

1. Open the repository's **Security** tab.
2. Select **Report a vulnerability**.
3. Submit your findings privately.

If that option is unavailable, open an issue titled **Request for a private security reporting channel** without including vulnerability details, exploit code, or sensitive information.

### What to Include

In your private report, include:

- A description of the vulnerability.
- The affected commit or version.
- Your Linux distribution, Python version, and nftables version.
- Steps to reproduce the issue in an isolated environment.
- Expected behavior and actual behavior.
- The potential security impact.
- A minimal example or suggested fix, if available.

Remove passwords, tokens, personal information, and sensitive network details from reports.

## Relevant Security Issues

Examples of issues worth reporting include:

- Configuration input causing unintended command or rule execution.
- Modification or deletion of unrelated firewall rules.
- Bypassing table ownership checks.
- Unexpected acceptance of traffic that should be blocked.
- Unsafe handling of privileged files or subprocesses.
- Failures in rule validation, atomic updates, or mutation locking.
- Restoration failures beyond the documented trial limitations.

## Safe Testing

- Test only on systems you own or have permission to assess.
- Use disposable VMs or an isolated lab.
- Keep local console access available when changing firewall rules.
- Avoid testing on production systems.
- Do not collect or publish other people's traffic.
- Do not disable unrelated security tools or flush the system ruleset.

## Security Design

Personal Guard is designed to:

- Validate configuration before generating rules.
- Execute subprocesses without using a shell.
- Preview rules by default.
- Require `--commit` for permanent application or removal.
- Check generated rules with nftables before installation.
- Apply updates atomically within nftables.
- Restrict mutations to its owned `inet personal_guard` table.
- Serialize cooperating application mutations using a lock.

These controls reduce risk but do not guarantee that every vulnerability has been eliminated.

## Known Limitations

### Administrator Privileges

Applying, inspecting, and removing kernel rules requires root privileges. Review the code and configuration before running commands with `sudo`.

### Trial Restoration

Trial mode runs in the foreground. It normally restores the previous configuration when its timer finishes or Ctrl+C is handled.

It is not an independent watchdog. Terminal closure, forced termination, system failure, or kernel errors can prevent restoration.

### Rule Behavior

- Loopback traffic is accepted before user-defined rules.
- Explicit rules run before established/related traffic handling.
- IPv6 ICMP is accepted by a built-in rule unless an earlier explicit rule matches.
- The sample configuration permits incoming UDP destination ports 68 and 546 for DHCP replies.
- Broad allow rules can weaken filtering.
- Rule changes can interrupt existing connections.

### Other Firewalls

Existing nftables rules and other firewall managers continue to affect traffic. Acceptance by Personal Guard does not override a drop elsewhere.

External firewall managers do not honor this application's mutation lock and may modify or remove its table.

### Coverage

The application filters local host IP traffic through input and output hooks. It does not provide:

- Native Windows firewall protection.
- Forwarded or bridged traffic filtering.
- Application or process-based filtering.
- URL or domain filtering.
- Malware detection.
- Packet payload inspection.
- Automatic persistence across reboot.

### Monitoring

Counters show packets and bytes matching rules. They do not identify attacks, malicious users, or unique connections.

A timeout alone does not prove that Personal Guard blocked a connection. Compare the relevant drop counter before and after a controlled test.

## Recovery

To remove Personal Guard's rules:

```bash
sudo python3 firewall.py disable --commit
```

If the application is unavailable, use a local console:

```bash
sudo nft delete table inet personal_guard
```

This removes only the project's table. Other firewall rules remain in place.

Do not use a system-wide `flush ruleset` command as a recovery step.

## Responsible Disclosure

Please allow time for a report to be investigated and a fix to be prepared before publishing technical details.

Any acknowledgement or credit should be agreed with the reporter. Reporting a vulnerability does not imply a financial reward.

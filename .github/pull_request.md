## Summary

Briefly describe what this pull request changes and why.

## Related Issue

Closes #

<!-- Remove this section if no issue is linked. -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Test improvement
- [ ] Refactoring
- [ ] Other:

## Changes Made

-
-
-

## Testing

Select only the checks you completed:

- [ ] Unit tests passed.
- [ ] Rule preview checked.
- [ ] Kernel validation passed.
- [ ] Trial restoration tested.
- [ ] Incoming filtering tested from another machine or VM.
- [ ] Outgoing filtering tested.
- [ ] Firewall removal tested.
- [ ] Documentation and links checked.

### Commands and Results

```text
Paste relevant commands and results here.
```

### Test Environment

- Linux distribution:
- Python version:
- nftables version:
- Physical machine or VM:
- Other firewall managers:

### Filtering Evidence

<!-- Complete for changes affecting packet filtering; otherwise write N/A. -->

- Rule or behavior tested:
- IPv4 / IPv6:
- Connectivity before applying the rule:
- Matching counter before and after:
- Connectivity after removing the rule:

A timeout alone does not prove blocking. Localhost traffic does not verify incoming filtering from another machine.

## Security Impact

Does this change affect privileges, input validation, subprocess execution, rule order, table ownership, or restoration behavior?

Describe the impact, or write “No security-related behavior changed.”

Do not include undisclosed vulnerability details. Follow SECURITY.md for private reporting.

## Compatibility and Limitations

- Breaking changes:
- New dependencies:
- Configuration changes:
- Untested behavior or known limitations:

<!-- Write N/A where appropriate. -->

## Checklist

- [ ] The change is focused and avoids unrelated edits.
- [ ] Documentation reflects any changed behavior.
- [ ] Relevant tests were added or updated where needed.
- [ ] No credentials, sensitive logs, or private network details are included.
- [ ] No generated archives, virtual environments, or Python cache files are included.
- [ ] Firewall changes remain limited to the project's owned table.
- [ ] No system-wide ruleset flush was introduced.
- [ ] Preview behavior and explicit commit requirements are preserved.
- [ ] Any changes to these safeguards are clearly explained above.

## Screenshots

<!-- Optional: add screenshots with sensitive information removed. -->

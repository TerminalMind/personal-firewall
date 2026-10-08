#!/usr/bin/env python3
"""Personal firewall: a dependency-free Python CLI for Linux nftables."""
import argparse
import ipaddress
import json
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager

TABLE = 'personal_guard'
OWNER = 'personal-guard-v1'


def validate(config):
    if not isinstance(config, dict) or set(config) != {'input_policy', 'output_policy', 'rules'}:
        raise ValueError('Config requires exactly input_policy, output_policy and rules')
    for direction in ('input', 'output'):
        if config[direction + '_policy'] not in ('accept', 'drop'):
            raise ValueError('Policies must be accept or drop')
    if not isinstance(config['rules'], list) or len(config['rules']) > 500:
        raise ValueError('rules must be a list of at most 500 rules')
    for rule in config['rules']:
        if not isinstance(rule, dict) or set(rule) - {'direction', 'action', 'protocol', 'remote', 'port'}:
            raise ValueError('Unknown rule fields')
        if rule.get('direction') not in ('input', 'output') or rule.get('action') not in ('accept', 'drop'):
            raise ValueError('Each rule needs direction input/output and action accept/drop')
        proto = rule.get('protocol', 'any')
        if proto not in ('any', 'tcp', 'udp', 'icmp', 'ipv6-icmp'):
            raise ValueError('Unsupported protocol')
        if 'port' in rule:
            if proto not in ('tcp', 'udp') or type(rule['port']) is not int or not 1 <= rule['port'] <= 65535:
                raise ValueError('port requires tcp/udp and an integer from 1 to 65535')
        if 'remote' in rule:
            if not isinstance(rule['remote'], str):
                raise ValueError('remote must be an IP or CIDR string')
            network = ipaddress.ip_network(rule['remote'], strict=False)
            if (proto == 'icmp' and network.version != 4) or (proto == 'ipv6-icmp' and network.version != 6):
                raise ValueError('Protocol and remote address families disagree')
    return config


def render(config):
    validate(config)
    lines = [f'table inet {TABLE} {{', f'  comment "{OWNER}";']
    for direction in ('input', 'output'):
        lines += [f'  chain {direction} {{',
                  f'    type filter hook {direction} priority 10; policy accept;',
                  f'    {"iifname" if direction == "input" else "oifname"} "lo" counter accept comment "loopback"']
        # Explicit rules precede connection tracking so blocks affect existing flows.
        for index, rule in enumerate(config['rules'], 1):
            if rule['direction'] != direction:
                continue
            parts = []
            if 'remote' in rule:
                net = ipaddress.ip_network(rule['remote'], strict=False)
                parts += ['ip' if net.version == 4 else 'ip6',
                          'saddr' if direction == 'input' else 'daddr', str(net)]
            proto = rule.get('protocol', 'any')
            if proto != 'any':
                parts += ['meta l4proto', proto]
            if 'port' in rule:
                parts += [proto, 'dport', str(rule['port'])]
            parts += ['counter', rule['action'], f'comment "rule-{index}"']
            lines.append('    ' + ' '.join(parts))
        lines += ['    ct state invalid counter drop comment "invalid"',
                  '    ct state established,related counter accept comment "return-traffic"',
                  '    meta l4proto ipv6-icmp counter accept comment "ipv6-control"',
                  f'    counter {config[direction + "_policy"]} comment "default-{direction}"',
                  '  }']
    return '\n'.join(lines + ['}', ''])


def nft(*args, script=None):
    executable = shutil.which('nft', path='/usr/sbin:/usr/bin:/sbin:/bin')
    if not executable:
        raise RuntimeError('nft not installed. On Ubuntu/Kali: sudo apt install nftables')
    result = subprocess.run([executable, *args], input=script, text=True,
                            capture_output=True, timeout=15)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'nft command failed')
    return result.stdout


def snapshot():
    tables = json.loads(nft('-j', 'list', 'tables'))['nftables']
    exists = any(x.get('table', {}).get('family') == 'inet' and
                 x.get('table', {}).get('name') == TABLE for x in tables)
    if not exists:
        return None
    data = json.loads(nft('-j', 'list', 'table', 'inet', TABLE))
    table = next(x['table'] for x in data['nftables'] if 'table' in x)
    if table.get('comment') != OWNER:
        raise RuntimeError('Reserved table is owned by another application; refusing to modify it')
    return nft('list', 'table', 'inet', TABLE)


def transaction(previous, replacement):
    return (f'delete table inet {TABLE}\n' if previous is not None else '') + replacement


@contextmanager
def lock():
    import fcntl
    # Root-owned directory avoids following an untrusted temporary-file symlink.
    directory = '/run/personal-guard'
    os.makedirs(directory, mode=0o700, exist_ok=True)
    st = os.lstat(directory)
    import stat
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or st.st_mode & 0o022:
        raise RuntimeError('Unsafe /run/personal-guard directory permissions')
    fd = os.open(directory + '/lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another firewall operation is running') from None
        yield


def status():
    if snapshot() is None:
        print('Firewall inactive (other system firewalls may still be active).')
        return
    data = json.loads(nft('-j', 'list', 'table', 'inet', TABLE))
    print(f'{"DIRECTION":10} {"RULE":20} {"PACKETS":>12} {"BYTES":>12}')
    for entry in data['nftables']:
        rule = entry.get('rule', {})
        for expr in rule.get('expr', []):
            if 'counter' in expr:
                count = expr['counter']
                print(f'{rule["chain"]:10} {rule.get("comment", ""):20} '
                      f'{count["packets"]:12} {count["bytes"]:12}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('preview', 'check', 'apply', 'trial'):
        p = sub.add_parser(name)
        p.add_argument('config')
        if name == 'apply':
            p.add_argument('--commit', action='store_true', help='Actually change kernel rules')
        if name == 'trial':
            p.add_argument('--seconds', type=int, default=30, choices=range(5, 301), metavar='5..300')
    sub.add_parser('status')
    p = sub.add_parser('monitor')
    p.add_argument('--interval', type=int, default=2, choices=range(1, 61), metavar='1..60')
    p = sub.add_parser('disable')
    p.add_argument('--commit', action='store_true')
    args = parser.parse_args(argv)
    try:
        script = None
        if hasattr(args, 'config'):
            with open(args.config, encoding='utf-8') as handle:
                script = render(json.load(handle))
        if args.command == 'preview' or (args.command == 'apply' and not args.commit):
            print(script)
            return 0
        if args.command == 'disable' and not args.commit:
            print(f'Preview only: delete table inet {TABLE}. Add --commit to execute.')
            return 0
        if sys.platform != 'linux' or os.geteuid() != 0:
            raise RuntimeError('This operation requires Linux and sudo/root')
        if args.command in ('status', 'monitor'):
            while True:
                print(time.strftime('%Y-%m-%d %H:%M:%S'))
                status()
                if args.command == 'status':
                    break
                time.sleep(args.interval)
            return 0
        with lock():
            old = snapshot()
            if args.command == 'disable':
                if old is not None:
                    nft('-f', '-', script=transaction(old, ''))
                print('Personal firewall disabled.')
                return 0
            batch = transaction(old, script)
            nft('--check', '-f', '-', script=batch)
            if args.command == 'check':
                print('Kernel validation passed; nothing changed.')
                return 0
            if args.command == 'trial':
                # finally also runs if Ctrl+C interrupts installation or waiting.
                try:
                    nft('-f', '-', script=batch)
                    print(f'Trial active for {args.seconds}s; Ctrl+C restores sooner.', flush=True)
                    time.sleep(args.seconds)
                finally:
                    current = snapshot()
                    restore = transaction(current, old or '')
                    if restore:
                        nft('-f', '-', script=restore)
                    print('Previous firewall configuration restored.')
            else:
                nft('-f', '-', script=batch)
                print('Firewall applied. Use status or monitor to see packet counters.')
        return 0
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import firewall as fw


def config(rules=None):
    return {'input_policy': 'drop', 'output_policy': 'accept', 'rules': rules or []}


class FirewallTests(unittest.TestCase):
    def test_reject_unsafe_input(self):
        for rule in [
            {'direction': 'input', 'action': 'accept; flush ruleset'},
            {'direction': 'output', 'action': 'drop', 'remote': '1.2.3.4; flush ruleset'},
            {'direction': 'input', 'action': 'drop', 'protocol': 'tcp', 'port': True},
            {'direction': 'input', 'action': 'drop', 'protocol': 'udp', 'port': 65536},
            {'direction': 'input', 'action': 'drop', 'port': 80},
            {'direction': 'input', 'action': 'drop', 'protocol': 'icmp', 'remote': '::1'},
            {'direction': 'input', 'action': 'drop', 'unknown': 'x'},
        ]:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                fw.render(config([rule]))

    def test_directions_families_and_precedence(self):
        text = fw.render(config([
            {'direction': 'input', 'action': 'drop', 'remote': '192.0.2.6/24'},
            {'direction': 'output', 'action': 'drop', 'remote': '2001:db8::/32', 'protocol': 'tcp', 'port': 443},
        ]))
        self.assertIn('ip saddr 192.0.2.0/24', text)
        self.assertIn('ip6 daddr 2001:db8::/32 meta l4proto tcp tcp dport 443', text)
        self.assertLess(text.index('rule-1'), text.index('ct state established'))
        self.assertNotIn('flush ruleset', text)

    def test_atomic_table_scoping(self):
        self.assertEqual(fw.transaction(None, 'new'), 'new')
        self.assertEqual(fw.transaction('old', 'new'), 'delete table inet personal_guard\nnew')

    def test_foreign_table_refused(self):
        outputs = [json.dumps({'nftables': [{'table': {'family': 'inet', 'name': fw.TABLE}}]}),
                   json.dumps({'nftables': [{'table': {'comment': 'someone-else'}}]})]
        with patch.object(fw, 'nft', side_effect=outputs), self.assertRaises(RuntimeError):
            fw.snapshot()

    def invoke(self, command, nft_error=None, interrupt=False):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'rules.json'
            path.write_text(json.dumps(config()))
            with patch.object(fw, 'nft', side_effect=nft_error) as nft, \
                 patch.object(fw, 'snapshot', side_effect=['OLD RULES', 'CURRENT RULES']), \
                 patch.object(fw, 'lock', contextlib.nullcontext), \
                 patch.object(fw.os, 'geteuid', return_value=0, create=True), \
                 patch.object(fw.sys, 'platform', 'linux'), \
                 patch.object(fw.time, 'sleep', side_effect=KeyboardInterrupt if interrupt else None), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = fw.main([*command, str(path)])
                return result, nft.call_args_list

    def test_preview_never_calls_kernel(self):
        result, calls = self.invoke(['apply'])
        self.assertEqual(result, 0)
        self.assertEqual(calls, [])

    def test_failed_check_never_installs(self):
        result, calls = self.invoke(['apply', '--commit'], RuntimeError('invalid'))
        self.assertEqual(result, 1)
        self.assertEqual(len(calls), 1)
        self.assertIn('--check', calls[0].args)

    def test_trial_restores_on_timeout_and_interrupt(self):
        for interrupted in (False, True):
            result, calls = self.invoke(['trial'], interrupt=interrupted)
            self.assertEqual(result, 130 if interrupted else 0)
            self.assertEqual(calls[-1].kwargs['script'], 'delete table inet personal_guard\nOLD RULES')


if __name__ == '__main__':
    unittest.main()

import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / 'bin/tmux-state-sync'
CAPACITY = '⚠ Selected model is at capacity. Please try a different model.'
IDLE = CAPACITY + '\n\n› Ask Codex to do anything\n\n  gpt-6-astra xhigh · ~ · Loudcue\n'


class StateSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = dict(os.environ, HOME=str(self.home))
        self.state = self.home / '.claude/agent-state/loudcue'
        self.state.parent.mkdir(parents=True)
        self.state.write_text('working\n')
        os.utime(self.state, (time.time() - 60, time.time() - 60))
        # Only external tmux/ps reads are doubled. The real executable owns state.
        fakebin = self.home / 'bin'
        fakebin.mkdir()
        self.env['PATH'] = str(fakebin) + ':' + os.environ['PATH']
        self.env['PANE_FIXTURE'] = str(self.home / 'pane')
        Path(self.env['PANE_FIXTURE']).write_text(IDLE)
        (fakebin / 'tmux').write_text('''#!/usr/bin/env python3
import os, sys
from pathlib import Path
args = sys.argv[1:]
if args[0] == 'list-sessions':
 if os.getenv('INVENTORY_FAIL'): sys.exit(1)
 print('loudcue')
elif args[0] == 'display': print('loudcue')
elif args[0] == 'list-panes':
 print('loudcue\\t%12\\t100\\t' + os.getenv('COPY_MODE', '0') + '\\tnode')
 if os.getenv('SECOND_PANE'): print('loudcue\\t%13\\t200\\t0\\tnode')
elif args[0] == 'capture-pane':
 if os.getenv('CAPTURE_FAIL'): sys.exit(1)
 print(Path(os.environ['PANE_FIXTURE']).read_text())
 if os.getenv('RACE'):
  import subprocess
  subprocess.run([os.environ['REAL_SYNC'], '--write-state', 'loudcue', os.environ['RACE']], check=True)
else: sys.exit(2)
''')
        (fakebin / 'ps').write_text('''#!/usr/bin/env python3
import os
print('100 1 node')
print('101 100 ' + ('claude' if os.getenv('CLAUDE') else '/opt/codex/bin/codex'))
''')
        for p in fakebin.iterdir(): p.chmod(0o755)
        self.env['REAL_SYNC'] = str(SYNC)

    def run_sync(self):
        subprocess.run([str(SYNC)], env=self.env, check=True, capture_output=True, timeout=10)
        return self.state.read_text().strip()

    def test_capacity_at_idle_prompt_needs_user(self):
        self.assertEqual(self.run_sync(), 'needs')

    def test_old_error_during_new_turn_stays_working(self):
        Path(self.env['PANE_FIXTURE']).write_text(IDLE + '\n› Try again\n• Working (esc to interrupt)\n')
        self.assertEqual(self.run_sync(), 'working')

    def test_error_quoted_in_output_stays_working(self):
        Path(self.env['PANE_FIXTURE']).write_text(IDLE.replace(CAPACITY, '  ' + CAPACITY))
        self.assertEqual(self.run_sync(), 'working')

    def test_successful_idle_prompt_not_treated_as_failure(self):
        Path(self.env['PANE_FIXTURE']).write_text(IDLE.replace(CAPACITY, '• Finished the job.'))
        self.assertEqual(self.run_sync(), 'working')

    def test_claude_pane_not_reconciled(self):
        self.env['CLAUDE'] = '1'
        self.assertEqual(self.run_sync(), 'working')

    def test_multiple_panes_not_reconciled(self):
        self.env['SECOND_PANE'] = '1'
        self.assertEqual(self.run_sync(), 'working')

    def test_fresh_prompt_not_reconciled(self):
        self.state.write_text('working\n')
        self.assertEqual(self.run_sync(), 'working')

    def test_capture_failure_leaves_state_alone(self):
        self.env['CAPTURE_FAIL'] = '1'
        self.assertEqual(self.run_sync(), 'working')

    def test_wrapped_preserved(self):
        self.state.write_text('wrapped\n')
        self.assertEqual(self.run_sync(), 'wrapped')

    def test_concurrent_new_prompt_wins(self):
        self.env['RACE'] = 'working'
        self.assertEqual(self.run_sync(), 'working')

    def test_concurrent_stop_wins(self):
        self.env['RACE'] = 'done'
        self.assertEqual(self.run_sync(), 'done')

    def test_copy_mode_does_not_read_old_screen(self):
        self.env['COPY_MODE'] = '1'
        self.assertEqual(self.run_sync(), 'working')

    def test_failed_inventory_preserves_existing_state(self):
        self.env['INVENTORY_FAIL'] = '1'
        self.assertEqual(self.run_sync(), 'working')

    def test_hook_prompt_then_failure_then_stop(self):
        import json
        env = dict(self.env, TMUX_PANE='%12')
        hook = ROOT / 'bin/codex-state-hook'
        def event(name):
            subprocess.run([str(hook)], input=json.dumps({'hook_event_name': name, 'cwd': str(self.home)}),
                           text=True, env=env, check=True, capture_output=True, timeout=10)
        event('SessionStart')
        self.assertEqual(self.state.read_text().strip(), 'idle')
        event('UserPromptSubmit')
        self.assertEqual(self.state.read_text().strip(), 'working')
        os.utime(self.state, (time.time() - 60, time.time() - 60))
        self.assertEqual(self.run_sync(), 'needs')
        event('UserPromptSubmit')
        self.assertEqual(self.state.read_text().strip(), 'working')
        event('Stop')
        self.assertEqual(self.state.read_text().strip(), 'done')
        event('SessionEnd')
        self.assertFalse(self.state.exists())

    def test_state_controls_wait_for_reconciliation_lock(self):
        import runpy
        from unittest.mock import patch
        with patch.dict(os.environ, self.env):
            sync = runpy.run_path(str(SYNC))
        controls = [([str(ROOT / 'bin/wrap'), 'loudcue'], 'wrapped'),
                    ([str(ROOT / 'bin/tmux-switch'), '--wrap-toggle', 'loudcue'], 'wrapped'),
                    ([str(SYNC), '--remove-state', 'loudcue'], None)]
        for args, expected in controls:
            with self.subTest(command=args):
                self.state.write_text('working')
                proc = None
                try:
                    with sync['state_lock']('loudcue'):
                        proc = subprocess.Popen(args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        with self.assertRaises(subprocess.TimeoutExpired):
                            proc.communicate(timeout=0.5)
                        self.assertEqual(self.state.read_text(), 'working')
                finally:
                    if proc is not None:
                        proc.communicate(timeout=5)
                self.assertEqual(proc.returncode, 0)
                actual = self.state.read_text().strip() if self.state.exists() else None
                self.assertEqual(actual, expected)

    def test_seed_and_prune_preserved(self):
        self.state.unlink()
        stale = self.state.parent / 'gone'
        stale.write_text('needs')
        self.assertEqual(self.run_sync(), 'idle')
        self.assertFalse(stale.exists())


if __name__ == '__main__': unittest.main()

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / 'bin/claude-state-hook'
BAR = '  ⏵⏵ bypass permissions on (shift+tab to cycle)'


class BackgroundBadgeTests(unittest.TestCase):
    """A turn end must not read `done` while the bottom bar shows background work."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        fakebin = self.home / 'bin'
        fakebin.mkdir()
        self.pane = self.home / 'pane'
        # Only tmux is doubled: display -> session name, capture-pane -> the pane fixture.
        (fakebin / 'tmux').write_text('''#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
if args[0] == 'display': print('test-session')
elif args[0] == 'capture-pane': sys.stdout.write(open(os.environ['PANE_FIXTURE']).read())
''')
        (fakebin / 'tmux').chmod(0o755)
        self.env = dict(os.environ, HOME=str(self.home), TMUX_PANE='%1',
                        PANE_FIXTURE=str(self.pane),
                        PATH=str(fakebin) + ':' + os.environ['PATH'])
        self.state = self.home / '.claude/agent-state/test-session'
        self.cwd = self.home / 'work'   # no .git -> un-gated, so a clean Stop writes `done`
        self.cwd.mkdir()

    def run_hook(self, payload, pane):
        self.pane.write_text(pane)
        subprocess.run([str(HOOK)], input=payload, text=True, env=self.env, check=True)
        return self.state.read_text().strip()

    def stop(self, pane):
        return self.run_hook('{"hook_event_name":"Stop","cwd":"%s"}' % self.cwd, pane)

    def idle_notification(self, pane):
        # The ~60s-idle Notification demotes `working` to `done` unless work is still open.
        self.state.parent.mkdir(parents=True, exist_ok=True)
        self.state.write_text('working\n')
        return self.run_hook(
            '{"hook_event_name":"Notification","message":"Claude is waiting for your input"}', pane)

    def test_monitor_badge_keeps_working(self):
        pane = 'Done for now.\n\n' + '  ⏵⏵ bypass permissions on · 1 monitor · ← 1 agent · ↓ to manage\n'
        self.assertEqual(self.stop(pane), 'working')

    def test_plural_monitors_keep_working(self):
        self.assertEqual(self.stop('ok\n' + BAR + ' · 2 monitors\n'), 'working')

    def test_monitor_spinner_form_keeps_working(self):
        pane = 'ok\n✻ Churned for 1s · done 7:55 AM · 1 monitor still running\n' + BAR + '\n'
        self.assertEqual(self.stop(pane), 'working')

    def test_existing_badges_still_keep_working(self):
        for badge in ('1 shell', '2 background tasks', '1 MCP task', '1 workflow'):
            with self.subTest(badge=badge):
                self.assertEqual(self.stop('ok\n' + BAR + ' · ' + badge + '\n'), 'working')

    def test_idle_notification_with_monitor_keeps_working(self):
        self.assertEqual(self.idle_notification('ok\n' + BAR + ' · 1 monitor\n'), 'working')

    def test_idle_notification_without_badge_is_done(self):
        self.assertEqual(self.idle_notification('ok\n' + BAR + '\n'), 'done')

    def test_agent_badge_alone_is_done(self):
        # "← 1 agent" shows on idle sessions too; it is not background work.
        self.assertEqual(self.stop('ok\n' + BAR + ' · ← 1 agent\n'), 'done')

    def test_monitor_in_prose_is_done(self):
        pane = 'I left · 1 monitor · running earlier.\n\n' + BAR + '\n'
        self.assertEqual(self.stop(pane), 'done')


if __name__ == '__main__':
    unittest.main()

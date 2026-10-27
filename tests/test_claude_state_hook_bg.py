import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / 'bin/claude-state-hook'
BAR = '  ⏵⏵ bypass permissions on (shift+tab to cycle)'
RULE = '─' * 40
# A finished-looking footer row: present so badge tests prove the badge, not the row.
ROW = '  ◆ example-workflow  ▮▮▮▮▮▮  2/2 · 3m05s · ↓ 10.0k tokens'


def box_pane(bar, box='❯ example prompt', rule_label='', row=ROW):
    """Prose, input box between two borders, mode bar, footer row."""
    bottom = RULE + (' ' + rule_label + ' ─' if rule_label else '')
    tail = (row + '\n') if row else ''
    return 'Example reply text.\n' + RULE + '\n' + box + '\n' + bottom + '\n' + bar + '\n' + tail


class HookCase(unittest.TestCase):
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
        self.transcript = self.home / '.claude/projects/example/session-1.jsonl'
        self.sdir = self.transcript.with_suffix('')

    def run_hook(self, payload, pane):
        self.pane.write_text(pane)
        payload = dict(payload, transcript_path=str(self.transcript))
        subprocess.run([str(HOOK)], input=json.dumps(payload, separators=(',', ':')),
                       text=True, env=self.env, check=True)
        return self.state.read_text().strip()

    def stop(self, pane):
        return self.run_hook({'hook_event_name': 'Stop', 'cwd': str(self.cwd)}, pane)

    def idle_notification(self, pane):
        # The ~60s-idle Notification demotes `working` to `done` unless work is still open.
        self.state.parent.mkdir(parents=True, exist_ok=True)
        self.state.write_text('working\n')
        return self.run_hook({'hook_event_name': 'Notification',
                              'message': 'Claude is waiting for your input'}, pane)

    def workflow(self, run_id, status=None, age_min=0):
        """Mimic Claude Code's run records: the script at launch, the status record at the end."""
        scripts = self.sdir / 'workflows/scripts'
        scripts.mkdir(parents=True, exist_ok=True)
        script = scripts / ('example-name-%s.js' % run_id)
        script.write_text('export const meta = {}\n')
        agents = self.sdir / 'subagents/workflows' / run_id
        agents.mkdir(parents=True, exist_ok=True)
        (agents / 'journal.jsonl').write_text('{}\n')
        if age_min:
            old = time.time() - age_min * 60
            for path in (script, agents / 'journal.jsonl', agents):
                os.utime(path, (old, old))
        if status:
            (self.sdir / 'workflows' / (run_id + '.json')).write_text(json.dumps({'status': status}))


class BadgeTests(HookCase):
    """A turn end must not read `done` while the chrome shows background work."""

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

    def test_badge_above_footer_row_keeps_working(self):
        # A footer row sits BELOW the mode bar, so the badge line is not the last line.
        self.assertEqual(self.stop(box_pane(BAR + ' · 1 monitor · ← 1 agent')), 'working')

    def test_comma_joined_badge_list_keeps_working(self):
        # Comma-only slot: neither item is followed by " ·" on its own.
        self.assertEqual(self.stop(box_pane(BAR + ' · 1 shell, 1 monitor · ← 1 agent')), 'working')

    def test_labelled_bottom_border_keeps_working(self):
        pane = box_pane(BAR + ' · 1 shell, 1 monitor', rule_label='example-label')
        self.assertEqual(self.stop(pane), 'working')

    def test_shell_mode_prompt_keeps_working(self):
        self.assertEqual(self.stop(box_pane(BAR + ' · 1 shell, 1 monitor', box='! echo example')), 'working')

    def test_trimmed_empty_prompts_keep_working(self):
        # tmux capture-pane trims the space after an empty prompt.
        for box in ('❯', '!'):
            with self.subTest(box=box):
                self.assertEqual(self.stop(box_pane(BAR + ' · 1 shell, 1 monitor', box=box)), 'working')

    def test_multiline_draft_with_dash_line_keeps_working(self):
        # A draft line starting "  ─" is input text, not the box border.
        pane = box_pane(BAR + ' · 1 shell, 1 monitor', box='❯ draft\n  ─ section heading\n  more text')
        self.assertEqual(self.stop(pane), 'working')

    def test_idle_notification_with_monitor_keeps_working(self):
        self.assertEqual(self.idle_notification('ok\n' + BAR + ' · 1 monitor\n'), 'working')

    def test_idle_notification_badge_above_footer_row_keeps_working(self):
        self.assertEqual(self.idle_notification(box_pane(BAR + ' · 1 shell, 1 monitor')), 'working')

    def test_idle_notification_without_badge_is_done(self):
        self.assertEqual(self.idle_notification(box_pane(BAR + ' · ← 1 agent')), 'done')

    def test_agent_badge_alone_is_done(self):
        # "← 1 agent" shows on idle sessions too; it is not background work.
        self.assertEqual(self.stop('ok\n' + BAR + ' · ← 1 agent\n'), 'done')

    def test_monitor_in_prose_is_done(self):
        pane = 'I left · 1 monitor · running earlier.\n\n' + BAR + '\n'
        self.assertEqual(self.stop(pane), 'done')

    def test_badge_text_in_prose_above_input_box_is_done(self):
        pane = 'Summary · 2 background tasks · completed\n' + box_pane(BAR + ' · ← 1 agent', row='')
        self.assertEqual(self.stop(pane), 'done')

    def test_badge_text_inside_input_box_is_done(self):
        # Only a recognised (labelled) bottom border keeps the draft out of the chrome.
        pane = box_pane(BAR + ' · ← 1 agent', box='❯ draft · 1 monitor · note', rule_label='example-label')
        self.assertEqual(self.stop(pane), 'done')

    def test_free_text_ending_in_badge_words_is_not_a_badge(self):
        # A permission dialog draws borders too, and may quote a command ending ", 1 monitor".
        pane = ('Example reply text.\n' + RULE + '\n Bash command\n\n   echo · Run a summary, 1 monitor\n'
                + RULE + '\n · Run a summary, 1 monitor\n Do you want to proceed?\n'
                + ' ❯ 1. Yes\n   2. Yes, and do not ask again\n   3. No\n\n Esc to cancel · Tab to amend\n')
        self.assertEqual(self.stop(pane), 'done')

    def test_dialog_with_full_badge_segment_is_done(self):
        # A permission dialog replaces the input box; its borders must not open a chrome region.
        pane = ('Example reply text.\n' + RULE + '\n Bash command\n\n   echo example\n'
                + RULE + '\n Summary · 2 background tasks · completed\n Do you want to proceed?\n'
                + ' ❯ 1. Yes\n   2. Yes, and do not ask again\n   3. No\n\n Esc to cancel · Tab to amend\n')
        self.assertEqual(self.stop(pane), 'done')

    def test_dialog_after_input_box_voids_chrome(self):
        pane = box_pane(BAR, row='') + RULE + '\n Summary · 2 background tasks · completed\n Esc to cancel\n'
        self.assertEqual(self.stop(pane), 'done')


class PayloadTaskTests(HookCase):
    """Stop's `background_tasks` list is authoritative whenever the payload carries it."""

    QUIET = box_pane(BAR + ' · ← 1 agent', row='')
    BUSY = box_pane(BAR + ' · 1 shell, 1 monitor · ← 1 agent')

    def stop_with(self, tasks, pane):
        return self.run_hook({'hook_event_name': 'Stop', 'cwd': str(self.cwd),
                              'background_tasks': tasks, 'session_crons': []}, pane)

    def test_listed_tasks_keep_working(self):
        for kind in ('workflow', 'monitor', 'shell', 'subagent', 'MCP task'):
            with self.subTest(kind=kind):
                tasks = [{'id': 't1', 'type': kind, 'status': 'running', 'description': 'example'}]
                self.assertEqual(self.stop_with(tasks, self.QUIET), 'working')

    def test_empty_list_is_done_even_with_a_badge_on_screen(self):
        # The registry is authoritative: a stale badge in the scrollback cannot pin `working`.
        self.assertEqual(self.stop_with([], self.BUSY), 'done')

    def test_crons_alone_are_done(self):
        payload = {'hook_event_name': 'Stop', 'cwd': str(self.cwd), 'background_tasks': [],
                   'session_crons': [{'id': 'c1', 'schedule': '*/5 * * * *', 'recurring': True,
                                      'prompt': 'example'}]}
        self.assertEqual(self.run_hook(payload, self.QUIET), 'done')

    def test_listed_task_seals_against_idle_notification(self):
        tasks = [{'id': 't1', 'type': 'workflow', 'status': 'running', 'name': 'example'}]
        self.assertEqual(self.stop_with(tasks, self.QUIET), 'working')
        self.assertEqual(self.idle_notification(self.QUIET), 'working')

    def test_later_empty_stop_releases_seal(self):
        tasks = [{'id': 't1', 'type': 'workflow', 'status': 'running', 'name': 'example'}]
        self.stop_with(tasks, self.QUIET)
        self.assertEqual(self.stop_with([], self.QUIET), 'done')
        self.assertEqual(self.idle_notification(self.QUIET), 'done')

    def test_missing_list_falls_back_to_badge(self):
        self.assertEqual(self.stop(self.BUSY), 'working')
        self.assertEqual(self.stop(self.QUIET), 'done')

    def test_malformed_list_falls_back_to_badge(self):
        payload = {'hook_event_name': 'Stop', 'cwd': str(self.cwd), 'background_tasks': 'oops'}
        self.assertEqual(self.run_hook(payload, self.BUSY), 'working')
        self.assertEqual(self.run_hook(payload, self.QUIET), 'done')


if __name__ == '__main__':
    unittest.main()

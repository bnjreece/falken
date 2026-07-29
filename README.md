# Falken

**The falcon over your fleet.** A tmux + [Claude Code](https://claude.com/claude-code) control layer for running *many* agent sessions at once without losing the thread.

When you're driving a dozen-plus Claude Code sessions across projects, the hard part isn't any single agent — it's knowing, at a glance, **which ones need you, which are working, and which are done.** Falken puts that on your tmux status bar, in a hot switcher, and (optionally) on physical LEDs.

## What it does

- **Live agent-state status bar** — every session reports its state via a Claude Code hook. Across the whole fleet the bar shows `✋ needs you` (with wait time, longest-first), `● working`, `✓ done`, `■ wrapped` (parked), a stacked proportion bar, and a session count. A `◉` dot goes red the moment anything needs you.
- **Hot switcher** (`Opt-s`) — an `fzf` popup of every session with live state, urgency-ordered. Jump by typing a name; filter by state (`^F` cycles presets, or type `f:working needs` for a custom multi-select); wrap or kill inline.
- **A real state model** — `needs` (blocked on a permission) · `working` · `done` (stopped, your call) · `wrapped` (you parked it) · `idle`. Plus sticky wrap, interrupt detection, and a **baking** state: a session running a background workflow keeps showing `working` while its subagents churn, instead of falsely reading `done`.
- **Quick keys** — jump to the next session that needs you, cycle the done pile, wrap/unwrap, help — all one chord.
- **SP-1 LED integration (optional)** — mirror the fleet onto a hardware controller: blink-cadence LEDs (needs = fast blink, working = pulse, done = solid, wrapped = off), Track buttons to jump between sessions, faders for fleet autopilot. See [`FELDD-CC-INTEGRATION.md`](FELDD-CC-INTEGRATION.md).

## How it works

Falken is a handful of small, fast shell scripts plus one Claude Code hook — no daemon required for the core (the LED integration is a separate, optional driver).

- A **Claude Code hook** (`bin/claude-state-hook`) writes each session's state to `~/.claude/agent-state/<session>` on every agent event.
- **tmux status scripts** (`bin/tmux-*`) read those files and render the bar, the reactive dot, and the switcher.
- Every script is a single-pass, fork-light design, so it stays snappy even with dozens of sessions hammering one tmux server.

## Install

```bash
git clone https://github.com/bnjreece/falken ~/falken
ln -s ~/falken/bin/* ~/bin/          # put the scripts on your PATH
```

Then wire the tmux keybinds + status line into `~/.tmux.conf`, and the hook into `~/.claude/settings.json`. [`FALKEN.md`](FALKEN.md) has the exact blocks and the full design log.

## Files

| Path | What |
|---|---|
| `bin/` | the scripts — status bar, reactive dot, hot switcher, hooks, splash |
| [`FALKEN.md`](FALKEN.md) | the full design log + backlog: what's built, what's parked, and why |
| [`FELDD-CC-INTEGRATION.md`](FELDD-CC-INTEGRATION.md) | the optional SP-1 hardware LED integration |
| [`SPLASH-CONCEPTS.md`](SPLASH-CONCEPTS.md) | boot-splash design explorations |

---

*[reece.is](https://reece.is) · the falcon over your fleet*

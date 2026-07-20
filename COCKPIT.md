# reece.is cockpit — what exists + backlog

A personal tmux + multi-agent control layer on the Mac mini. Scripts live in `~/bin`, config in `~/.tmux.conf` + `~/.claude/settings.json`. Full usage: run `reece-help` (or `Opt-i`).

## What's built (2026-07-20)
- **Splash** — `reece` (full) / `reece --quick` (short, plays on new `cs`/`csd` sessions) / `reece --loop`.
- **Agent-state status bar** — every session shows: `◉ reece.is` (dot turns red on any `✋`), `✋ needs (named, wait-time, longest-first)`, `● working (named)`, `✓ done (count)`, `■ wrapped (count)`, `N sess`, clock.
  - Driven by `~/bin/claude-state-hook` (a Claude Code hook) → `~/.claude/agent-state/<session>` → `~/bin/tmux-agent-state`.
- **Reactive dot** — `~/bin/tmux-reece-dot`.
- **Keys** (primary = Opt-letter, fallback = C-a+Shift): `Opt-n` next needs · `Opt-m` cycle done · `Opt-w` wrap · `Opt-i` help · `C-a U` un-wrap.
  - `~/bin/tmux-jump-needs`, `~/bin/tmux-jump-done`, `~/bin/wrap`, `~/bin/reece-help`.
- **State semantics:** `✋` needs = agent blocked (Notification/PermissionRequest) · `✓` done = agent stopped (still your call) · `■` wrapped = you parked it (`Opt-w`).
- **AI delegation** — `codex-runner` skill (`~/.claude/skills/`): from any session, "get Sol's take" → OpenAI Codex on ChatGPT Pro. Full multi-agent Room: `~/bnjmn/the-room/SPEC.md`.

## BACKLOG (parked ideas)

### 📱 Phone push on `✋` (parked 2026-07-20 — build when wanted)
When a session flips **idle/done → needs** (`✋`), push a notification to the iPhone so you can walk away and still get pulled back.
- **Approach:** have `claude-state-hook` detect the *transition* into `needs` (compare previous state before overwriting) and, only on that edge, fire an `ntfy` publish. iPhone shows it via the ntfy app or Apple push.
- **Transport options:** (a) `ntfy.sh` public topic with a random/secret name (zero infra); (b) self-hosted ntfy on the mini, tailnet-only via Tailscale (most private). Given the Tailscale setup, (b) fits the privacy posture.
- **Details:** include session name + how long it's been waiting; **dedupe** (fire once per idle→needs edge, not repeatedly); maybe a "still waiting 15m" nudge; respect a quiet-hours window.
- **Effort:** ~30–45 min. **Open Qs:** ntfy.sh vs self-hosted; quiet hours; whether to also cover `csd` sessions.

### Other parked ideas
- **`◉` dot pulse** — animate the reece dot (blink) when something needs you, not just static red.
- **Rate-limit meter** — Max window % + Sol window % in the status bar (from a ledger).
- **Unify with SP-1 LEDs** — same hook state drives the feldd-cc LEDs + this bar (one cockpit, physical + software).
- **macOS desktop notification** on `✋` (local, no phone needed).
- **`csd` red danger theme** — red status bar when in a skip-permissions session.
- **Denylist guard** — `csd` refuses to launch in `rise`/`estate`/`vendr-work`.
- **fzf session picker** — bare `cs` → fuzzy-pick to attach.
- **Worktree mode** — `cs --wt <branch>` = git worktree + session.
- **Auto-wrap** idle sessions after N hours.
- **Digest command** — summarize all `✓ done` sessions at once.
- **Full-screen dashboard TUI** — the cockpit as a dedicated view, not just the status line.

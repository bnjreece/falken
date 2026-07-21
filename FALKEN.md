# Falken — what exists + backlog
*The falcon over your fleet · reece.is/falken*

A personal tmux + multi-agent control layer on the Mac mini. Scripts live in `~/bin`, config in `~/.tmux.conf` + `~/.claude/settings.json`. Full usage: run `reece-help` (or `Opt-i`).

## What's built (2026-07-20)
- **Splash** — `reece` (full) / `reece --quick` (short, plays on new `cs`/`csd` sessions) / `reece --loop`.
- **Agent-state status bar** — every session shows: `◉ reece.is` (dot turns red on any `✋`), `✋ needs (named, wait-time, longest-first)`, `● working (named)`, `✓ done (count)`, `■ wrapped (count)`, `N sess`, clock.
  - Driven by `~/bin/claude-state-hook` (a Claude Code hook) → `~/.claude/agent-state/<session>` → `~/bin/tmux-agent-state`.
- **Reactive dot** — `~/bin/tmux-reece-dot`.
- **Hot switcher** — `Opt-s` (or `C-a Tab`) pops an `fzf` popup listing ALL sessions with live state, urgency-ordered; arrow/⏎ to jump, **type to filter** (e.g. "feld"). This is the general navigator (`~/bin/tmux-switch`); the rotation keys below are just quick-shortcuts for the two common cases.
- **Keys** (primary = Opt-letter, fallback = C-a+Shift): `Opt-s` switcher (inside: `^W` wrap-toggle · `^X` kill) · `Opt-n` next needs · `Opt-m` cycle done · `Opt-w` wrap⇄unwrap toggle · `Opt-i` help · `C-a W`/`C-a U` force wrap/unwrap.
  - `~/bin/tmux-switch`, `~/bin/tmux-jump-needs`, `~/bin/tmux-jump-done`, `~/bin/wrap`, `~/bin/reece-help`.
- **State semantics:** `✋` needs = agent blocked on you (a *permission* request) · `●` working · `✓` done = agent stopped (still your call) · `■` wrapped = you parked it (`Opt-w`) · `○` idle.
  - **Fix 2026-07-20:** Claude Code's `Notification` hook fires BOTH for permission requests AND for 60s-idle — the hook now reads the message and only flags `✋` on real permission asks, so background-workflow / bypass-permission sessions no longer false-alarm.
- **AI delegation** — `codex-runner` skill (`~/.claude/skills/`): from any session, "get Sol's take" → OpenAI Codex on ChatGPT Pro. Full multi-agent Room: `~/bnjmn/the-room/SPEC.md`.

## BACKLOG (parked ideas)

### 📱 Phone push on `✋` (parked 2026-07-20 — build when wanted)
When a session flips **idle/done → needs** (`✋`), push a notification to the iPhone so you can walk away and still get pulled back.
- **Approach:** have `claude-state-hook` detect the *transition* into `needs` (compare previous state before overwriting) and, only on that edge, fire an `ntfy` publish. iPhone shows it via the ntfy app or Apple push.
- **Transport options:** (a) `ntfy.sh` public topic with a random/secret name (zero infra); (b) self-hosted ntfy on the mini, tailnet-only via Tailscale (most private). Given the Tailscale setup, (b) fits the privacy posture.
- **Details:** include session name + how long it's been waiting; **dedupe** (fire once per idle→needs edge, not repeatedly); maybe a "still waiting 15m" nudge; respect a quiet-hours window.
- **Effort:** ~30–45 min. **Open Qs:** ntfy.sh vs self-hosted; quiet hours; whether to also cover `csd` sessions.

### Other parked ideas
- **Help/switcher = FALKEN wordmark, no animation** (do once the new wordmark is picked) — `Opt-i` must go STRAIGHT to help (drop the `falken --quick` splash preamble in `reece-help-view`); the help header shows the new **FALKEN** wordmark, not the old REECE.IS cyan art. **Rule: the full logo + animation is seen ONLY when spawning a new session (`cs`/`csd`); help + switcher use static small wordmarks. Status bar keeps `reece.is` (the brand).**
- **`◉` dot pulse** — animate the reece dot (blink) when something needs you, not just static red.
- **📊 Usage meter (far-right of status bar)** — spec'd 2026-07-20. Show current-window token usage for Claude + Sol. **No official rate-limit % is exposed by either CLI**, so show **raw window tokens** (honest); add `% of a budget you set` later if wanted.
  - **Claude:** use **`ccusage`** (`npx ccusage@latest blocks --active --json`, or `brew install ccusage`) → active 5h-block `totalTokens`. **Do NOT hand-parse `~/.claude/projects/*.jsonl` naively** — cache-read tokens + whole-session histories inflate it to *billions* (verified: a quick parse returned 37B). Let ccusage do the windowing + token formula.
  - **Sol:** parse `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` → `total_token_usage` (running per-session total); sum today's/active rollouts. Caveat: only counts Sol runs **on the mini**, not phone/other ChatGPT.
  - **Architecture:** a **60s cron** updater writes a cache (`~/.falken/usage`); the `status-right` segment just **reads the cache** (never run node every 1s).
  - **Display:** `⧗ CLA 1.2M · SOL 340k` (raw), far right. **Effort ~30-45 min; build fresh** (self-contained, correctness-sensitive).
- **Unify with SP-1 LEDs** — same hook state drives the feldd-cc LEDs + this bar (one board, physical + software).
- **macOS desktop notification** on `✋` (local, no phone needed).
- **`csd` red danger theme** — red status bar when in a skip-permissions session.
- **Denylist guard** — `csd` refuses to launch in `rise`/`estate`/`vendr-work`.
- **fzf session picker** — bare `cs` → fuzzy-pick to attach.
- **Worktree mode** — `cs --wt <branch>` = git worktree + session.
- **Auto-wrap** idle sessions after N hours.
- **Digest command** — summarize all `✓ done` sessions at once.
- **Full-screen dashboard TUI** — Falken as a dedicated view, not just the status line.

## Repo layout & wiring
**This repo IS Falken.** Scripts are canonical here in `bin/` and **symlinked into `~/bin`** (single source of truth — edit here, git-tracked). The config that wires them lives in `$HOME` (not tracked here):
- **Scripts** — `bin/*` ⇄ `~/bin/*` (symlinks): `reece` splash · `reece-help` + `reece-help-view` cheatsheet (esc/q closes) · `tmux-switch` hot switcher (type-filter, `^X` kill, `◉ reece.is` label) · `tmux-agent-state` status-right · `tmux-reece-dot` reactive dot · `tmux-state-sync` seed+prune · `tmux-jump-needs`/`tmux-jump-done` rotation · `wrap` park · `claude-state-hook` the Claude→state bridge.
- **tmux** — `~/.tmux.conf`: status-left/right call the scripts, `status-interval 1`, the `--- Falken · reece.is agent board ---` + hot-switcher keybind blocks (Opt-s/n/m/w/i + C-a fallbacks).
- **Claude Code** — `~/.claude/settings.json`: `claude-state-hook` on 6 events (UserPromptSubmit / Notification / PermissionRequest / Stop / SessionStart / SessionEnd).
- **State** — `~/.claude/agent-state/<session>` (runtime files, not tracked; auto seeded/pruned by `tmux-state-sync`).

Rehome on a new machine: clone this repo, symlink `bin/*`→`~/bin`, paste the Falken keybind block + the settings.json hook.

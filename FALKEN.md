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
- **Background-work state (`done` vs still-baking)** — a session with a live background task (a `Monitor`, background `Bash`, running build) shows `done` because its agent turn ended (`Stop` hook), even though work continues; it only flips back to `working` when the task pings.
  - **INVESTIGATED & PARKED 2026-07-21 — no clean signal exists.** The `Stop` hook payload carries **no** `backgroundTasksRunning` field (`stop_hook_active` is hook re-entry control, not task state); there is **no** background-task-completion hook (a finished bg task just re-wakes the agent as a fresh turn, indistinguishable from a human prompt); `~/.claude/tasks/<session>/` holds only `.highwatermark`+`.lock`, not a live registry. Every detection path is fragile or partial: transcript-tailing (internal format, race-prone, misses `Monitor`), `ps` process-tree (catches a `run_in_background` Bash's real child PID but misses in-process `Monitor`/subagents), or a cooperative marker file (only clean option, but the agent must write/clear it per task — not automatic). A wrong auto-`baking` lies as badly as a wrong `done`, and `wrap` already parks a session by hand. **Decision: leave `done` honest-about-the-turn; do NOT ship a heuristic.** Revisit only if Claude Code adds a `backgroundTasksRunning` field to the Stop payload or a `BackgroundTaskCompleted` hook (worth a `/feedback` request).
- **Full write-sandbox (confine Claude to `~/bnjmn/bnjmn/`)** — the OS filesystem sandbox (`sandbox.filesystem.allowWrite`), allow-listing `[~/bnjmn, ~/.claude, ~/.codex, $TMPDIR]` so Claude can only *write* inside projects + its own machinery (closes the Bash read/write vector the deny-list can't). **Test in a scratch session first** — too-tight allow-list breaks the hooks/Falken/feldd-cc. Deny-list (secrets + sensitive project dirs) is already LIVE in `~/.claude/settings.json` (survives `csd`).
  - **RESEARCHED 2026-07-21, PARKED pending scope decision.** Verified against `code.claude.com/docs/en/sandboxing.md` (CC 2.1.216). Key facts: (1) sandbox gates **Bash + subprocesses only** (macOS Seatbelt) — `Edit`/`Read`/`Write` tools use the permission/deny-list, NOT the sandbox. So the sandbox's real win is the **Bash-reads-secrets** vector the deny-list can't touch (`bash -c 'cat ~/.ssh/id_rsa'`), via `sandbox.credentials.files:[{path,mode:deny}]` + `filesystem.denyRead`. (2) Schema: `sandbox.enabled:true` + `filesystem.{allowWrite,denyWrite,denyRead,allowRead,disabled}`; **sandbox path prefixes differ from permission rules** — `/abs`, `~/home`, `./proj-relative` (NOT the `//abs` of Read/Edit rules). Default writable = cwd+subdirs + session `$TMPDIR`; default read = whole disk (incl. secrets!). (3) **Enabling the sandbox also turns ON network isolation** (there's `filesystem.disabled` but no `network.disabled`) — new domains prompt/block, which under `csd` ("nothing replaces the prompt") can break `curl localhost:9200` feldd-cc, npm/builds, `git push`, `op`. Neutralize via `network.allowedDomains` (localhost + your hosts). (4) **Under `csd` the sandbox is toothless unless strict mode**: a blocked write triggers a `dangerouslyDisableSandbox` retry that just runs under bypass — set `allowUnsandboxedCommands:false` for teeth (then out-of-allowlist writes hard-fail). (5) `~/.claude/settings.json` is auto-write-protected from sandboxed Bash regardless. **OPEN Qs to verify in a scratch `cs` session before global:** does the sandbox apply under `csd` at all; are Claude Code hooks (claude-state-hook) sandboxed (would need `~/.claude/agent-state` in allowWrite); does loopback survive network isolation (feldd-cc). **Scope decision pending** (asked user): (A) FS-confine + net-open [recommended], (B) full FS+net lockdown, (C) harden deny-list only, skip OS sandbox.
- ~~📊 Usage meter~~ — **DROPPED 2026-07-21.** No official API exposes subscription rate-limit %, and a token count vs a self-set budget drifts unknowably from the real limit. Not worth building something that lies. (Anthropic/OpenAI Usage APIs cover *API-key* billing, not Max/Pro subscriptions.)
- ✅ **Unify with SP-1 LEDs — LIVE 2026-07-21** (feldd-cc extended to state-watch `agent-state`; blink-cadence LEDs + button map + global faders — see `FELDD-CC-INTEGRATION.md`).
- **SP-1 track ↔ software UI** (discussing) — surface feldd-cc's 4 Track-LED assignments (the 4 MRU sessions) back INTO the switcher + status bar: badge which sessions are on tracks ❶–❹, and show the current session's track. Needs feldd-cc to write its board mirror to a file (e.g. `~/.claude/agent-tracks`) the UI reads.
- **macOS desktop notification** on `✋` (local, no phone needed).
- **`csd` red danger theme** — red status bar when in a skip-permissions session.
- **Denylist guard** — `csd` refuses to launch in sensitive project dirs.
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

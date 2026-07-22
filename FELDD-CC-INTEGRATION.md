# Falken ↔ feldd-cc (SP-1) integration — spec

Physical face of Falken: the SP-1's LEDs mirror fleet state; its buttons act on sessions.
Grounded in a code-level research pass of `~/bnjmn/feldd-sp1-firmware/feldd-cc/` (branch `wireless-console`), 2026-07-21.

## Reality-checks that reshaped the design
1. **LEDs are MONOCHROME** — 8 single-color PWM LEDs (`firmware/app/src/led.h`), no RGB/palette. State = *pattern* (on/off/blink) + *which* LED. The Falken jewel palette does NOT apply to hardware.
2. **No pulse/breathe** — shipped firmware honors ON/OFF only; `bri`/`blink`/`ms` fields are dropped (`firmware/app/src/protocol.c:396-417`). The daemon's "working=breathe" renders as plain **solid** → currently indistinguishable from `done`. Fake motion host-side via on/off toggling (blink cadence).
3. **feldd-cc already IS a state→LED + button→command bridge** for Claude sessions (daemon `feldd_cc.py`, running PID-tracked, BLE, cockpit mode). It reconstructs state from Claude hook events (`/hook` on `:9200`), NOT from Falken's `~/.claude/agent-state/` files, and it has no concept of `wrapped`.

## Architecture: EXTEND feldd-cc — do not build a competing bridge
- feldd-cc is the **single owner** of the SP-1 transport (BLE now; USB ports free). A separate Falken bridge would contend for the link. So extend feldd-cc rather than build a parallel process.
- Make feldd-cc a true **Falken mirror**: read `~/.claude/agent-state/<session>` (written by `~/bin/claude-state-hook`) as authoritative state — it already resolves pane→session, so add a state-file read. This is the "state-watch" model, and it gives feldd-cc `wrapped` for free + keeps one source of truth (same file the bar/switcher read).

## LED language — blink cadence (the only lever firmware honors)
| Falken state | LED |
|---|---|
| **needs** | **fast blink** (~3-4 Hz) |
| **working** | **pulse / breathe** (smooth) |
| **done** | **solid** |
| **wrapped / idle** | **off** |
- **NOTE — pulse WORKS on Benjamin's device.** The research read the *repo* firmware (concluded breathe→solid), but the *flashed* firmware renders a nice pulse. Trust the device; verify against the flashed firmware, not repo source.
- Fixes the working-vs-done collision (both solid today would be indistinguishable).
- Position (feldd already does this): Track LEDs `0-3` = front/active sessions (MRU); side LEDs `4-7` = overflow/bench. `needs` auto-promotes a session to a front Track LED.

## Buttons — bidirectional (CONFIRMED)
Since we're *editing feldd-cc*, every button is rebindable (the config-only play/vol±/fwd/rwd limit doesn't apply).
- **Track 1-4** = jump to the 4 tracked (most-recent) sessions. *(keep)*
- **FWD / RWD** = **triage jog** — step forward/back through everything wanting you: **needs (oldest→newest) then dones (oldest→newest)**, one combined cycle.
- **Vol- = wrap · Vol+ = unwrap** the focused session.
- **Play = "continue"** into the terminal — currently `["continue","Enter"]` (one click types + sends). Keep one-click-send (optional future: two-stage click-to-stage / double-to-send).
- `run_button_action` runs `{"shell": cmd}`, `cwd = focused session cwd`, 10s timeout (`feldd_cc.py:836-862`).

## Faders (4 × 0-127) — FINAL (global, Claude-Code-focused)
**All GLOBAL/fleet-wide.** Per-session was rejected: non-motorized faders can't chase sessions that swap in/out under them, you'd never know which fader owns which agent, and a fresh session could inherit a hot leash → dangerous. A global fader always means exactly one thing.

| # | fader | low ↔ high |
|---|---|---|
| **1** | **Autopilot on/off** | bottom = no auto-continue · top = auto-continue the fleet |
| **2** | **Autopilot duration** | bottom = 5 min · mid = ~1 hr · top = forever — how long it runs before stopping to check in (bounded-autonomy safety valve) |
| **3** | **Scroll *within*** the focused session | scrub back through that agent's output (grab-and-scrub; absolute-over-variable = feel, not precise) |
| **4** | **Scroll *across*** the fleet | sweep a highlight across all sessions (LED brightens as you pass); press Play to jump |

- **3 + 4 are a pair:** *down into* one session vs *sideways across* all of them.
- **Optional:** fold 1+2 into one fader (off → 5m → 1h → forever) to free a slot; kept separate for the explicit on/off switch.
- **Rejected:** Effort (global "think hard" for all sessions is wrong), DND, per-session anything (swap/motorization), live-rig/lights/volume (keep it Claude-Code-only).
- **Gotcha:** absolute 0-127 faders → the LED is the readout, the fader is input-only; use soft-takeover / grab-to-set.

## Confirmed decisions
1. ✅ **State-watch `~/.claude/agent-state/`** — one source of truth; gives `wrapped`.
2. ✅ **LED cadence** needs=fast-blink · working=**pulse** · done=solid · wrapped/idle=off. (Front Track LEDs track the last-4 sessions → off is rare there, which is fine.)
3. ✅ **Button map** above (Track=jump · FWD/RWD=triage jog · Vol±=wrap/unwrap · Play=continue).
4. ✅ **Transport stays feldd-cc-on-BLE**; extend feldd-cc, no separate bridge.
5. ✅ **Faders** (global): autopilot on/off · duration · scroll-within · scroll-across. Per-session / effort / DND / live-rig all rejected.

## Gotchas (design around these)
- **Override is sticky** — the bridge must `led_release()` on every exit or the LEDs freeze.
- **MIDI mode required** (`••`+Track4) or presses double-type into the Mac.
- **BLE:** pair in macOS System Settings; attach via CoreBluetooth `retrieveConnectedPeripherals` (not scan).
- **Side LEDs 4-7** addressable like main ones, *unless* a `FELDD_MODE_LED_SINGLE` firmware build is flashed (folds them to one pin). Confirm the build.
- Push ≤20 Hz, dedupe unchanged frames, 20-byte ATT MTU.
- **Pane-less hooks = phantom Track LEDs (FIXED 2026-07-21).** Falken is a *tmux* fleet board. A hook with no `$TMUX_PANE` (an auto-memory write from `~/.claude/projects/.../memory` firing SessionStart/Notification) minted a `tmux`-less board record named from the cwd basename (`memory`) that **neither prune could evict** (both key off a tmux name) — it fast-blinked a Track LED forever. Fix: `settings.json` `/hook` curls guard on `$TMUX_PANE` (like `claude-state-hook` already did) **and** `apply_hook` drops pane-less hooks under Falken. Only tmux-bound sessions ever claim a Track LED.

## Key files
`feldd_cc.py` (daemon + `/hook` + render loop + button dispatch) · `sp1_console/protocol.py` (wire codec) · `sp1_console/transport.py` + `cb_transport.py` (USB/BLE) · `firmware/app/src/{protocol.c,led.c,led_override.c}` (device truth) · `~/bin/claude-state-hook` (writes `agent-state`).

## Follow-on: SP-1 track ↔ software UI (spec'd 2026-07-21 · confirmed)
Close the loop — surface feldd-cc's 4 Track-LED assignments back onto the screen so the physical box and the software UI always agree.

**Data — feldd-cc writes a file the UI reads (chosen: by far the best):**
- feldd-cc writes `~/.claude/agent-tracks` whenever its board assignment changes — up to 4 lines, `<n>\t<session>` (n=1..4 = the MRU Track-LED sessions; omit empty slots). Same cheap pattern as `agent-state`.
- NOT HTTP: the status bar renders every 1s — a `curl /config` per tick adds latency + a hard dependency on the daemon. A file read is instant + decoupled.

**Display (confirmed):**
- **Switcher — all four:** in `tmux-switch` `list()`, read `agent-tracks` and append a **plain, distinct badge `[1]`–`[4]`** to the 4 tracked sessions. Color = NOT a fleet-state color (e.g. cream `230`, bold) so it reads as "on the physical box." Other 16 sessions unbadged.
- **Status bar — current only:** a small `bin/tmux-track-badge <session>` reads `agent-tracks` for the passed session → prints `[N]` (bright) or nothing. Wire into `status-left`: `... [#S]#(/Users/bnjmn/bin/tmux-track-badge #{session_name}) `.

**Build steps:**
1. feldd-cc: write `~/.claude/agent-tracks` on board change (edit near the LED-assignment / board-mirror code; `/restart` to apply — the daemon is live). Do it on a branch, merge, `POST /restart`.
2. new `bin/tmux-track-badge` (reads agent-tracks → emits `[N]`), symlink into `~/bin`.
3. `tmux-switch`: badge the 4 tracked in `list()`.
4. `~/.tmux.conf`: add the badge `#()` to `status-left`.

**Confirmed decisions:** bar = current session's track only · switcher = all four · badge = plain-but-distinct `[N]` · data = feldd-cc-writes-file (not HTTP).

## Fleet-authoritative board + live/offline status (SHIPPED 2026-07-22)
Two fixes after the board pinned *wrapped* sessions to Track LEDs while live ones sat off-board:
- **Registration gap.** The board was hook-driven: a session started AFTER the daemon whose hooks arrive pane-less never registered, so feldd-cc never knew your active sessions and wrapped ones squatted the Tracks. `discover_new_sessions()` now runs **every state-watch pass** (not just at startup), pulling in any live `claude` tmux pane, seeded from its `agent-state` file. ADD-ONLY (skips known panes/names → never clobbers a live state to idle). The board follows the whole tmux fleet.
- **Squatter gap.** Front-row self-correction was purely edge-driven (`_reclaim_front` / `_pull_active_to_front`) with timing holes. `_rebalance_front()` runs each pass: the 4 Track LEDs always hold the most-recently-active **non-parked** (working/done/needs) sessions; a wrapped/idle front session yields to any live one waiting on the bench/off-board. Stable in steady state (no LED churn).
- **Live/offline status.** `/config` now returns `link: {up, transport}` (fed by `_on_link`). `tmux-track-badge` mirrors it into `~/.claude/feldd-status` (`live` | `nodevice` | `offline`); the switcher shows a top banner (`● feldd-cc live` / `◐ SP-1 disconnected` / `○ daemon down`) and **dims the `[N]` badges** when the box isn't actually being driven, so a stale track map never looks authoritative. `+5 tests (119 pass)`.

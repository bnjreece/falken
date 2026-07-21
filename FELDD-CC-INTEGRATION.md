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

## Key files
`feldd_cc.py` (daemon + `/hook` + render loop + button dispatch) · `sp1_console/protocol.py` (wire codec) · `sp1_console/transport.py` + `cb_transport.py` (USB/BLE) · `firmware/app/src/{protocol.c,led.c,led_override.c}` (device truth) · `~/bin/claude-state-hook` (writes `agent-state`).

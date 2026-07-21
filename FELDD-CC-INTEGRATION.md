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

## Faders (4 × 0-127) — brainstorm, TBD
Currently `autopilot` preset; repurpose for Falken. Candidate uses:
- **DND / focus dial** — slide down to hush/dim the board (stop flashing) when heads-down; up to re-arm.
- **Fleet scrubber** — slide across the session list to preview/highlight; press to jump.
- **Live-rig control** — "live from the mini": fader = studio-light dimmer (existing amaran BLE) or stream volume.
- **Auto-wrap patience** — how long a done/idle session waits before auto-parking.
- *(Gotcha: absolute 0-127 faders have a pickup/takeover jump; use soft-takeover for continuous controls.)*

## Confirmed decisions
1. ✅ **State-watch `~/.claude/agent-state/`** — one source of truth; gives `wrapped`.
2. ✅ **LED cadence** needs=fast-blink · working=**pulse** · done=solid · wrapped/idle=off. (Front Track LEDs track the last-4 sessions → off is rare there, which is fine.)
3. ✅ **Button map** above (Track=jump · FWD/RWD=triage jog · Vol±=wrap/unwrap · Play=continue).
4. ✅ **Transport stays feldd-cc-on-BLE**; extend feldd-cc, no separate bridge.
5. ⏳ **Faders** — see brainstorm.

## Gotchas (design around these)
- **Override is sticky** — the bridge must `led_release()` on every exit or the LEDs freeze.
- **MIDI mode required** (`••`+Track4) or presses double-type into the Mac.
- **BLE:** pair in macOS System Settings; attach via CoreBluetooth `retrieveConnectedPeripherals` (not scan).
- **Side LEDs 4-7** addressable like main ones, *unless* a `FELDD_MODE_LED_SINGLE` firmware build is flashed (folds them to one pin). Confirm the build.
- Push ≤20 Hz, dedupe unchanged frames, 20-byte ATT MTU.

## Key files
`feldd_cc.py` (daemon + `/hook` + render loop + button dispatch) · `sp1_console/protocol.py` (wire codec) · `sp1_console/transport.py` + `cb_transport.py` (USB/BLE) · `firmware/app/src/{protocol.c,led.c,led_override.c}` (device truth) · `~/bin/claude-state-hook` (writes `agent-state`).

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
| **working** | **slow blink** (~0.5-1 Hz) |
| **done** | **solid** |
| **wrapped / idle** | **off** |
- Fixes the working-vs-done collision (both solid today).
- Position (feldd already does this): Track LEDs `0-3` = front/active sessions (MRU); side LEDs `4-7` = overflow/bench. `needs` auto-promotes a session to a front Track LED.

## Buttons — bidirectional (partly there already)
- Cockpit already binds: **Track 1-4 = jump to that session**, **Vol+ = next-needs**, **Play = nudge/continue**.
- Free to bind (config: play/vol±/fwd/rwd; Track1-4 reserved): **Vol-, FWD, RWD**.
  - Proposed: **FWD = wrap current** (`wrap -t <session>`), **RWD = cycle done** (like Opt-m), **Vol- = jump next-needs** (or keep as-is).
- `run_button_action` runs `{"shell": cmd}` with `cwd = active session cwd`, 10s timeout (`feldd_cc.py:836-862`).

## Open decisions
1. **State source:** state-watch `agent-state/` (recommended — gives `wrapped`, one source of truth) vs keep event-push + add a wrap hook.
2. **off = wrapped AND idle** (confirmed: no color, so `off` is the only "parked" signal; `done` stays solid-lit until reviewed).
3. **Button map:** which of Vol-/FWD/RWD → wrap / cycle-done / next-needs?
4. **Transport stays feldd-cc-on-BLE.** The standalone Falken bridge idea is dropped — feldd-cc is the bridge.

## Gotchas (design around these)
- **Override is sticky** — the bridge must `led_release()` on every exit or the LEDs freeze.
- **MIDI mode required** (`••`+Track4) or presses double-type into the Mac.
- **BLE:** pair in macOS System Settings; attach via CoreBluetooth `retrieveConnectedPeripherals` (not scan).
- **Side LEDs 4-7** addressable like main ones, *unless* a `FELDD_MODE_LED_SINGLE` firmware build is flashed (folds them to one pin). Confirm the build.
- Push ≤20 Hz, dedupe unchanged frames, 20-byte ATT MTU.

## Key files
`feldd_cc.py` (daemon + `/hook` + render loop + button dispatch) · `sp1_console/protocol.py` (wire codec) · `sp1_console/transport.py` + `cb_transport.py` (USB/BLE) · `firmware/app/src/{protocol.c,led.c,led_override.c}` (device truth) · `~/bin/claude-state-hook` (writes `agent-state`).

# Falken — splash concepts (brainstormed by Fable 5)

Three directions for the Falken splash/logo. All art alignment-verified in a real terminal; every line
is safe to emit with `printf '%s\n' '<line>'`. Color via truecolor `\033[38;2;R;G;Bm … \033[0m`.

---

## Concept 1 — "HIGH WATCH" (the falcon's scope)
A round radar scope; the fleet is blips under a slow sweep. The eye is the scope origin; the session
list sits beside it like a tower log. **Vibe: instrument.**

Palette: phosphor green `51;255;102` (rim, names, healthy `◉`); dim green `17;102;51` (range dots,
sweep trail `┊`, footer); radar cyan `0;229;255` (sweep arm `╱`, wordmark); alert amber `255;176;0`
(`▲` blip + `NEEDS YOU`); white-hot `230;255;240` (one-frame flash as sweep crosses a blip).

```
         ▁▄▀▀▀▀▀▀▀▄▁
      ▄▀▔    ┊     ▔▀▄        F A L K E N · high watch
    ▄▀   ·   ┊   ╱    ▀▄      ─────────────────────────
   ▐         ┊ ╱   ▲    ▌     ◉ feldd      building
   ▐  ·      ◉      ·   ▌     ◉ myapp    ok
   ▐       ·     ·      ▌     ◉ website    idle
    ▀▄        ·       ▄▀      ▲ scraper    NEEDS YOU
      ▀▄▁         ▁▄▀
         ▔▀▄▄▄▄▄▄▄▀▔          4 aloft · sweep 12s
```

Animation: 8 frames ~150ms, looping. Cyan sweep arm rotates clockwise around center `◉`; previous
position becomes the dim-green trail. Blip flashes white-hot for one frame as the arm passes. The amber
`▲` ignores the sweep and pulses on its own 2-frame cycle — the thing that needs you never stops
blinking; the `NEEDS YOU` line blinks in sync.

Why: a raptor circling *is* a slow rotating scan; a radar sweep is that gesture in 80s command-center
language. WarGames mood (quiet room, scope, mostly-fine blips) with no map and no quotable reference.
Honest about the mechanism: sessions = blips, sweep = poll loop, amber = swoop.

---

## Concept 2 — "ON STATION" (vector falcon over the grid)
A wireframe falcon from directly above, holding position over a perspective grid of session territory;
one cell glows because something moved. **Vibe: creature.**

Palette: TRON teal `0;255;214` (wing strokes, bright at body); deep teal `0;122;107` (wingtips fade —
vector glow falloff); grid blue `41;98;255` (perspective grid); ember orange `255;111;0` (hot `▒` cell,
eye `◉`, talons `▼`); pale cyan `179;255;244` (wordmark). Color wing rows in 3 steps so the bird looks
phosphor-bloomed at center.

```
  ╲▁▁▁                                         ▁▁▁╱
      ▔▔▔╲▁▁▁                           ▁▁▁╱▔▔▔
             ▔▔▔╲▁▁▁     ▗▄▖     ▁▁▁╱▔▔▔
                    ▔▔▔◥▟▘◉▝▙◤▔▔▔
                         ▐█▌
                          ▼
       ───────┬───────┬───────┬───────┬───────
            ╱        ╱ ▒▒▒▒▒▒▒ ╲        ╲
          ╱         ╱ ▒▒▒▒▒▒▒▒▒ ╲        ╲
                 F A L K E N · on station
```

Animation: ~12 frames, looping. (1) Hover: falcon shifts one column left/center/right/center — a slow
hunting hover; wingtips feather via `╲▁`/`▁╲`. (2) Cell pulse each frame: `░→▒→▓→▒` ember. (3) Optional
stinger every N loops: falcon drops one row/frame toward the hot cell, wings narrowing, then cuts to the
session picker — the stoop *is* the transition into the tool.

Why: purest expression of the name — bird of prey above a TRON-era grid territory, sessions as land.
Teal-and-orange light-cycle palette with zero TRON iconography (the orange is prey movement, not a rival
program). The stoop-as-transition makes the logo *enact* what Falken does.

---

## Concept 3 — "RESEARCH TERMINAL rev 8.3" (amber phosphor boot)
The machine in a reclusive professor's lab warming up: an amber CRT boot ROM draws the FALKEN wordmark
under scanline static, walks a checklist, parks on a live block cursor. **Vibe: machine voice.**

Palette: bright amber `255;176;0` (wordmark top, `▸` arrows, header); mid amber `204;122;0` (wordmark
mid, labels, dot leaders); dark amber `122;74;0` (wordmark bottom — vertical fade, `░` static, rule);
terminal green `51;255;51` (results only — `OK`, `aloft`, `ARMED`); soft white `255;236;204` (cursor `▊`).

```
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  FALKEN RESEARCH TERMINAL                 rev 8.3

   █▀▀▀ ▄▀▀▄ █    █ ▄▀ █▀▀▀ █▄ █
   █▀▀  █▀▀█ █    █▀▄  █▀▀  █ ▀█
   ▀    ▀  ▀ ▀▀▀▀ ▀  ▀ ▀▀▀▀ ▀  ▀
   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ reece.is/falken

   ▸ tmux uplink ................. OK
   ▸ fleet scan .................. 6 sessions aloft
   ▸ talon reflex ................ ARMED
   ▸ operator watch .............. ▊
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

Animation: one-shot boot (~2s) → idle loop. (1) Static bands + header flicker (tube warming). (2)
Wordmark wipes in top→mid→bottom, each row in its gradient shade (scanline reveal). (3) Checklist types
on one line at a time; dot leaders fill left-to-right, green result snaps in. (4) Idle: `▊` blinks at
500ms; every ~4s one drawn row dims for a frame (interlace flicker, the CRT breathing).

Why: leans on Dr. Falken the man — a private lab bench, one amber terminal, a checklist by someone who
names subsystems *talon reflex*. 1983 through texture (phosphor fade, dot leaders, rev number), zero
quotable references. Ends on "operator watch … `▊`" — the machine is now the one paying attention.

---

**How they differ:** #1 = an *instrument* (circular scope, rotation, green/cyan). #2 = a *creature*
(figurative vector, hover/dive, teal/orange). #3 = a *machine voice* (pure typography, type-on, amber+green).
Each compresses to a minimal splash: #1's scope alone, #2's falcon alone, or #3's 3-row wordmark alone.

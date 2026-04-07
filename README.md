# BuddyMon

A Gen V animated Pokémon desktop buddy for Windows. Lives on your taskbar, walks around, and uses moves with particle effects.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **Professor Oak's lab** — polished animated selection screen to choose your starter
- **Three Kanto starter lines** — full evolution chains (Bulbasaur → Ivysaur → Venusaur, etc.)
- **Gen V animated sprites** — the classic Black & White pixel art style
- **1-in-100 shiny chance** — on every spawn, evolution, and reroll
- **12 move effects** — 4 unique particle/vector animations per starter line
- **Physics** — gravity, walking, wall bouncing, drag-to-reposition
- **Everything via right-click** — no extra windows, all controls on the sprite

## Installation

```bash
pip install Pillow
python buddymon.py
```

Sprites download automatically on first run (~18 small GIFs, ~1 MB total, cached in `sprites/`).

## Usage

1. Run `python buddymon.py`
2. Pick your starter from Professor Oak's lab table
3. Your buddy drops onto the taskbar and starts walking

**Right-click the sprite** for all controls:

| Option | Description |
|---|---|
| Evolve / Devolve | Cycle through the 3-stage evolution line |
| Use Move | Trigger an animated move effect |
| Change Starter | Switch to a different starter line (resets to stage 1) |
| Reroll Shiny | Re-roll the 1/100 shiny chance |
| Throw Up | Launch the buddy into the air |
| Quit | Close the app |

## Move Effects

| Bulbasaur line | Charmander line | Squirtle line |
|---|---|---|
| Vine Whip — animated vines | Ember — fire sparks | Water Gun — water stream |
| Razor Leaf — flying leaf polygons | Flamethrower — cone of fire | Bubble — rising hollow circles |
| Solar Beam — charge glow + beam | Dragon Rage — expanding rings | Bite — snapping jaw arcs |
| Sleep Powder — drifting purple dust | Scratch — slash marks | Withdraw — shell pulse |

## Requirements

- **Windows** — uses Windows-specific transparency APIs
- **Python 3.8+**
- **Pillow** — `pip install Pillow`

## Credits

- Sprites: [PokeAPI](https://github.com/PokeAPI/sprites) — Gen V Black & White animated sprites
- Pokémon and all related names are © Nintendo / Game Freak. This is a fan project, not affiliated with or endorsed by Nintendo.

## License

MIT — see [LICENSE](LICENSE) for details.

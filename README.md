# Football 3D

A lightweight football game built with **Pygame**, featuring an isometric-style view, responsive controls, and arcade-inspired gameplay mechanics.

## Overview

Football 3D is a small game project focused on creating a fast, playable football experience using Python and Pygame. The project includes core match mechanics such as passing, shooting, tackling, player switching, stamina management, and restart logic, along with several quality-of-life improvements for gameplay and presentation.

The game is currently implemented in **Pygame** as the main playable version. A separate `panda3d_foundation/` directory is included as an early starter for a possible future 3D migration.

## Features

- Isometric-style football gameplay
- Player movement, passing, crossing, shooting, and tackling
- Through-pass mechanic
- Player switching
- Stamina system for the controlled player
- Radar / minimap
- Pause and restart functionality
- Fullscreen toggle
- HUD and gameplay polish
- Improved restart logic for correct goal kicks and corners
- Initial Panda3D foundation for future 3D expansion

## Tech Stack

- **Python**
- **Pygame**

## Why Pygame

The project remains on **Pygame** by design. Since the game relies on a single active display loop and tightly integrated gameplay logic, introducing another engine such as Panda3D, Arcade, or Ren'Py into the main runtime would add unnecessary complexity and instability.

Pygame provides a practical and reliable foundation for the current version of the game.

## Controls

| Action | Key |
|--------|-----|
| Move | `WASD` / Arrow Keys |
| Sprint | `Z` |
| Pass | `SPACE` |
| Through Pass | `Q` |
| Cross | `C` |
| Shoot | Hold `F` or `Shift`, release to shoot |
| Tackle | `X` |
| Switch Player | `TAB` |
| Pause / Resume | `P` |
| Restart Match | `R` |
| Fullscreen Toggle | `F11` |
| Quit | `ESC` |

## Installation

Clone the repository and install the dependencies:

```bash
pip install -r requirements.txt

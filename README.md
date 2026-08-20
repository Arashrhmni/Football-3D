# Football 3D — Modular Match & League Engine (Advanced Prototype)

A high-performance 11v11 football simulation featuring a custom top-down orthographic projection, autonomous agent AI, and a full **League Phase** and **Champions League** season framework. Built from scratch using Python and Pygame.

## 🕹️ Game Modes

* **Quick Play** — Pick any two clubs from all 6 leagues and jump straight into a match.
* **League Mode** — Run a full single-league season: round-robin fixtures, automated matchday simulation, and live standings.
* **Champions League** — Modern 36-team UCL-style format: an 8-match league phase, a 2-legged play-off round, then Round of 16 → Quarter-finals → Semi-finals → Final.

## 🚀 Technical Architecture & Features

### 1. League Phase & Season Simulation
The engine supports a full competitive season framework:
* **Dynamic Fixture Generation**: Implements a standard **Round-Robin "Circle Method"** algorithm to generate balanced Home/Away schedules for leagues of varying sizes (18 to 20 teams).
* **League Hub & Persistence**: A centralized hub manages the season state, tracking fixtures and real-time standings across the season.
* **Advanced Standings Logic**: Tables are calculated and sorted using FIFA-standard tie-breaking rules: Points → Goal Difference → Goals For.
* **Match Simulation**: Integrated an automated simulation engine for non-player matches, allowing for full-season progression.

### 2. Champions League Mode
* **36-Team League Phase**: Each club plays 8 matches against varied opponents; the top 8 qualify directly for the Round of 16, teams 9–24 enter a 2-legged knockout play-off, and the bottom 12 are eliminated.
* **Full Knockout Bracket**: Round of 16 (2-legged) → Quarter-finals → Semi-finals → Final (single-leg), with every tie the human isn't part of simulated automatically.

### 3. Top-Down Orthographic Projection & Physics
* **Verticality**: Ball physics include a $wz$ height variable for realistic parabolic arcs during crosses, corners, and through-balls — lifted visually on screen without skewing the pitch itself.
* **Lead-Passing Engine**: Pass logic calculates a lead vector based on teammate velocity:
    $$LeadPos = TargetPos + (TargetVelocity \times LeadFactor)$$

### 4. Humanoid Animation & Kit Framework
* **Procedural Animation**: Player limbs use sine-wave based procedural animation synchronized with velocity vectors.
* **Dynamic Kits**: Supports 114 unique club identities across 6 leagues (England, Spain, Germany, Italy, Portugal, Netherlands) with style-aware rendering (Stripes, Sashes, and Half-and-Half designs).

## ⚖️ Portfolio-Safe Compliance
To align with professional open-source standards, this project utilizes **IP-Safe Fictional Branding** (e.g., *FC Blaugrana*, *Sky Blues FC*, *Los Blancos CF*) while maintaining the visual inspiration of major European clubs.

## 🎮 Controls

| Action | Key | Details |
| :--- | :--- | :--- |
| **Move** | `WASD` / Arrows | 8-way directional movement |
| **Sprint** | `Z` | Increases speed; consumes stamina |
| **Pass** | `SPACE` | Direct lead-pass to teammate |
| **Through Pass** | `Q` | Weight-based pass into open space |
| **Cross** | `C` | High-arc ball from wide areas |
| **Shoot** | `F` / `Shift` | Hold to charge power bar |
| **Tackle** | `X` | Proximity-based challenge |
| **Pause / Menu** | `P` / `ESC` | Access match settings or quit to menu |
| **Restart** | `R` | Quick-restart current match state |
| **Fullscreen** | `F11` | Toggle display mode |

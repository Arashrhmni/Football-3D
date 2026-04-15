# Football 3D — Modular Match & League Engine (Advanced Prototype)

A high-performance 11v11 football simulation featuring **Isometric 3D projection**, autonomous agent AI, and a comprehensive **League Phase** system. Built from scratch using Python and Pygame.

## 🚀 Technical Architecture & Features

### 1. League Phase & Season Simulation
The engine now supports a full competitive season framework:
* **Dynamic Fixture Generation**: Implements a standard **Round-Robin "Circle Method"** algorithm to generate balanced Home/Away schedules for leagues of varying sizes (18 to 22 teams).
* **League Hub & Persistence**: A centralized hub manages the season state, tracking 380+ fixtures and real-time standings.
* **Advanced Standings Logic**: Tables are calculated and sorted using FIFA-standard tie-breaking rules: Points → Goal Difference → Goals For.
* **Match Simulation**: Integrated an automated simulation engine for non-player matches, allowing for full-season progression.

### 2. Custom Isometric Projection & Physics
* **Verticality**: Ball physics include a $wz$ height variable for realistic parabolic arcs during crosses, corners, and through-balls.
* **Lead-Passing Engine**: Pass logic calculates a lead vector based on teammate velocity:
    $$LeadPos = TargetPos + (TargetVelocity \times LeadFactor)$$

### 3. Humanoid Animation & Kit Framework
* **Procedural Animation**: Player limbs use sine-wave based procedural animation synchronized with velocity vectors.
* **Dynamic Kits**: Supports 60+ unique club identities with style-aware rendering (Stripes, Sashes, and Half-and-Half designs).

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

## 🛠️ Installation & Run

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/Football-3D.git](https://github.com/YOUR_USERNAME/Football-3D.git)
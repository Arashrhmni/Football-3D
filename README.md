# Football 3D — Isometric 11v11 Engine (Modular Edition)

An advanced, modular 11v11 football simulation featuring **Isometric 3D projection**, multi-layered AI systems, and decoupled component architecture.

## 🚀 Technical Architecture
The project has been refactored into a modular system to improve maintainability and scalability:
* **`ai.py`**: Manages goalkeeper logic, team-wide attacking shapes, and defensive lane-blocking.
* **`ball.py` & `player.py`**: Decoupled physics entities for 3D trajectory calculation and humanoid procedural animation.
* **`pitch.py`**: A high-performance rendering module that "bakes" the 1260x810 field to a static surface.
* **`game.py`**: The core engine managing set-piece state transitions and collision detection.

## ✨ New Technical Improvements

### 1. Lead-Passing Engine
Unlike basic "lock-on" passing, the new pass logic calculates a **lead vector**:
$$LeadPos = TargetPos + (TargetVelocity \times LeadFactor)$$
The ball is kicked toward where the player is heading, allowing for fluid "tiki-taka" build-up play.

### 2. Set-Piece & Kickoff Constraints
* **Kickoff Freeze**: Implemented a 1.5s physics lock to ensure players maintain formation integrity before the whistle.
* **Forced Throw-In Logic**: Resuming play from the sidelines now requires a forced pass, preventing "self-dribbling" and adhering to professional football rules.
* **Goalkeeper Time-Management**: AI Keepers now feature a 2-second hold timer, after which they are forced to distribute the ball to prevent "soft-locks."

### 3. Enhanced CPU Build-Up
The CPU now utilizes a `cpu_attacking_shape()` system:
* **Defensive Line**: Full-backs overlap or stay back depending on ball position.
* **Midfield Triangles**: Players move dynamically to offer passing lanes to the ball carrier.
* **Diagonal Runs**: Forwards perform diagonal channel runs to stretch the user's defense.

## 🎮 Updated Controls
| Action | Key | Details |
| :--- | :--- | :--- |
| **Move** | WASD / Arrows | Physics-based movement |
| **Pass** | SPACE | **Lead Pass** to teammate in stride |
| **Shoot** | F / L-Shift | Charges power; fires from any field position |
| **Cross** | C | Lofts a high ball into the box from wide areas |
| **Tackle** | X | Contextual defensive challenge |

## 🛠️ Installation
1. Clone: `git clone https://github.com/Arashrhmni/Football-3D.git`
2. Install: `pip install pygame`
3. Run: `python main.py`
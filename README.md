# Football 3D — Isometric 11v11 Engine

A lightweight, high-performance 2D football simulation using **Isometric 3D projection** and custom AI behaviors. Built from scratch using Python and Pygame.

## 🚀 Key Technical Features

### 1. Custom Isometric Projection Engine
The game uses a mathematical transformation to map 3D world coordinates (x, y, z) onto a 2D screen plane.
* **Verticality:** Ball physics include a `wz` (height) variable, allowing for realistic parabolic arcs, bounces, and headers.
* **Optimization:** The pitch and stadium markings are "baked" onto a static surface during initialization to maintain a consistent **60 FPS**.

### 2. Advanced Agent AI
* **Dynamic Positioning:** Teammates utilize "run-into-channel" logic, positioning themselves based on the ball carrier's location to create passing triangles.
* **Goalkeeper Intelligence:** Keepers use intercept logic to track the ball's trajectory and move laterally to cut off shooting angles.
* **Opposition Pressure:** CPU opponents use a proximity-based state machine to switch between "Halt Shape," "Press," and "Tackle" modes.

### 3. Physics & Gameplay
* **3D Ball Physics:** Includes gravity, ground friction, and lofted pass mechanics.
* **Tactical Controls:** Features sprint mechanics, power-charging for shots, and defensive tackling cooldowns.

## 🎮 Controls
| Action | Key |
| :--- | :--- |
| **Move** | Arrow Keys / WASD |
| **Sprint** | Z (hold) |
| **Pass** | SPACE |
| **Shoot** | F / Left-Shift (Hold to charge power) |
| **Tackle** | X |
| **Switch Player** | TAB |
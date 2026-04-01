# Football 3D — Isometric 11v11 Engine (Advanced Prototype)

A high-performance 11v11 football simulation featuring **Isometric 3D projection**, autonomous agent AI, and custom humanoid animations. Built from scratch using Python and Pygame.

## 🚀 Key Technical Features

### 1. Custom Isometric Projection & World Physics
The engine maps a 3D coordinate system ($wx, wy, wz$) onto a 2D screen plane using trigonometric transformations.
* **Verticality:** Ball physics include a $wz$ height variable, enabling realistic parabolic arcs for crosses, corners, and lofted shots.
* **Expanded Environment:** A professional-grade 1260×810 pitch including a "runoff" area, full 3D goal boxes with net grid lines, and regulation markings such as penalty arcs and 6-yard boxes.
* **Optimization:** Static stadium geometry is "baked" onto a separate surface during initialization to ensure a locked **60 FPS**.

### 2. Advanced Agent AI & Build-Up Play
The AI has evolved from simple "ball-chasing" to a tactical systems-based approach:
* **Build-Up Logic:** The CPU prioritizes space-aware passing triangles and forward runs over solo dribbling.
* **Positional Defending:** Defenders actively block passing lanes and maintain a defensive line based on the ball’s position rather than just rushing the carrier.
* **Reaction Delay System:** To simulate organic movement, players have a staggered reaction cooldown after passes or turnovers, preventing instantaneous pivots.

### 3. Humanoid Animation System
Players are modeled as multi-part 3D figures rather than simple ellipses:
* **Procedural Animation:** Legs and arms are animated to swing in sync with movement speed.
* **Directional Awareness:** Heads and eyes rotate to face the direction of movement or the ball.
* **Team Identities:** Authentic **Barcelona** (Blaugrana stripes) vs. **Real Madrid** (White/Gold) kits, including team-specific goalkeeper colors.

### 4. Dynamic Set-Pieces & Quality of Life
* **Animated Set-Pieces:** Features fully animated throw-ins and corner kicks where players physically walk to the ball to perform the action.
* **Auto-Switching:** Includes "Auto-Switch on Pass" and "Auto-Switch on Tackle" logic, ensuring the user always maintains control of the most relevant player.

## 🎮 Controls

| Action | Key | Details |
| :--- | :--- | :--- |
| **Move** | Arrow Keys / WASD | 8-way directional movement |
| **Sprint** | Z (hold) | Increases speed but reduces turn radius |
| **Pass** | SPACE | Targeted pass to the best-positioned teammate |
| **Cross** | C | Whip a high-arc ball into the box from wide areas |
| **Shoot** | F / L-Shift | Hold to charge the power bar |
| **Tackle** | X | Proximity-based defensive challenge |
| **Switch Player**| TAB | Manual toggle to the nearest teammate |
| **Quit** | ESC | Safe exit |
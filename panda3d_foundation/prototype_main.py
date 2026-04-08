"""Panda3D foundation scene for a future full migration.

This is intentionally separate from the working Pygame game.
It proves the rendering direction and scene structure for a later full port.
"""
from math import sin, cos

try:
    from direct.showbase.ShowBase import ShowBase
    from direct.task import Task
    from panda3d.core import CardMaker, LineSegs, NodePath, Vec3
except Exception as exc:  # pragma: no cover - optional runtime dependency
    raise SystemExit(
        "Panda3D is not installed. Run: pip install panda3d"
    ) from exc

from constants import W_W, W_H, W_MX, W_MY


class PandaPitchDemo(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(0.08, 0.20, 0.08, 1.0)

        self.cam_heading = 0.0
        self.cam_dist = 1100.0
        self.cam_height = 700.0
        self.time = 0.0

        self.accept('escape', self.userExit)
        self.accept('arrow_left', self._spin, [-4.0])
        self.accept('arrow_right', self._spin, [4.0])
        self.accept('arrow_up', self._zoom, [-60.0])
        self.accept('arrow_down', self._zoom, [60.0])

        self._build_pitch()
        self._build_goals()
        self._build_markers()
        self.taskMgr.add(self._tick, 'football-demo-tick')
        self._update_camera()

    def _spin(self, delta):
        self.cam_heading += delta
        self._update_camera()

    def _zoom(self, delta):
        self.cam_dist = max(450.0, min(1800.0, self.cam_dist + delta))
        self._update_camera()

    def _update_camera(self):
        ang = self.cam_heading * 0.0174533
        self.camera.setPos(
            W_MX + cos(ang) * self.cam_dist,
            W_MY + sin(ang) * self.cam_dist,
            self.cam_height,
        )
        self.camera.lookAt(W_MX, W_MY, 0)

    def _build_pitch(self):
        cm = CardMaker('pitch')
        cm.setFrame(0, W_W, 0, W_H)
        pitch = self.render.attachNewNode(cm.generate())
        pitch.setP(-90)
        pitch.setPos(0, 0, 0)
        pitch.setColor(0.16, 0.55, 0.16, 1.0)

        lines = LineSegs('lines')
        lines.setThickness(3.0)
        lines.setColor(1, 1, 1, 1)
        rect = [(0,0), (W_W,0), (W_W,W_H), (0,W_H), (0,0)]
        for (x1,y1), (x2,y2) in zip(rect, rect[1:]):
            lines.moveTo(x1, y1, 1.0)
            lines.drawTo(x2, y2, 1.0)
        lines.moveTo(W_MX, 0, 1.0)
        lines.drawTo(W_MX, W_H, 1.0)
        self.render.attachNewNode(lines.create())

    def _build_goals(self):
        for x in (0, W_W):
            goal = LineSegs(f'goal-{x}')
            goal.setThickness(4.0)
            goal.setColor(1, 1, 1, 1)
            depth = -35 if x == 0 else 35
            top = W_MY - 72
            bot = W_MY + 72
            goal.moveTo(x, top, 0)
            goal.drawTo(x, bot, 0)
            goal.drawTo(x + depth, bot, 0)
            goal.drawTo(x + depth, top, 0)
            goal.drawTo(x, top, 0)
            self.render.attachNewNode(goal.create())

    def _marker(self, parent: NodePath, pos, color):
        cm = CardMaker('marker')
        cm.setFrame(-10, 10, -10, 10)
        node = parent.attachNewNode(cm.generate())
        node.setP(-90)
        node.setColor(*color, 1.0)
        node.setPos(pos[0], pos[1], 4.0)
        return node

    def _build_markers(self):
        self.players_a = []
        self.players_b = []
        for i in range(5):
            self.players_a.append(self._marker(self.render, (180 + i*90, 180 + i*70), (0.1, 0.4, 0.9)))
            self.players_b.append(self._marker(self.render, (W_W - 180 - i*90, 180 + i*70), (0.9, 0.9, 0.9)))
        self.ball = self._marker(self.render, (W_MX, W_MY), (1.0, 0.7, 0.1))
        self.ball.setScale(0.6)

    def _tick(self, task):
        self.time += globalClock.getDt()
        self.ball.setPos(W_MX + sin(self.time * 1.4) * 180, W_MY + cos(self.time * 1.1) * 120, 8)
        return Task.cont


if __name__ == '__main__':
    PandaPitchDemo().run()

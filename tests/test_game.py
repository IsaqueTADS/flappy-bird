import random
import unittest

from game import BIRD, World, GROUND, GAP, PIPE_WIDTH, BIRD_X


class PhysicsTests(unittest.TestCase):
    def make_world(self):
        return World(random.Random(42))

    def test_flap_then_gravity(self):
        world = self.make_world()
        world.flap()
        world.step(1/60)
        self.assertLess(world.y, 190)
        initial_velocity = world.velocity
        world.step(1/60)
        self.assertGreater(world.velocity, initial_velocity)

    def test_floor_and_ceiling_collisions(self):
        for y in (5, GROUND-5):
            world = self.make_world()
            world.y = y
            world.step(0)
            self.assertTrue(world.dead)

    def test_pipe_collision_and_safe_gap(self):
        for y, dead in ((200, False), (200-GAP/2-5, True), (200+GAP/2+5, True)):
            world = self.make_world()
            world.pipes[0].update(x=BIRD_X-PIPE_WIDTH/2, center=200)
            world.y = y
            world.step(0)
            self.assertEqual(world.dead, dead)

    def test_score_only_once(self):
        world = self.make_world()
        world.pipes[0].update(x=BIRD_X-PIPE_WIDTH-1)
        world.step(0)
        world.step(0)
        self.assertEqual(world.score, 1)

    def test_pipe_recycling_preserves_spacing(self):
        world = self.make_world()
        world.pipes[0]["x"] = -100
        world.step(0)
        self.assertEqual(len(world.pipes), 3)
        self.assertEqual(world.pipes[-1]["x"]-world.pipes[-2]["x"], 170)

    def test_dead_world_stays_still(self):
        world = self.make_world()
        world.dead = True
        state = world.y, world.pipes[0]["x"]
        world.flap()
        world.step(1)
        self.assertEqual((world.y, world.pipes[0]["x"]), state)

    def test_sprite_rows_have_consistent_width(self):
        self.assertEqual({len(row) for row in BIRD}, {17})


if __name__ == "__main__":
    unittest.main()

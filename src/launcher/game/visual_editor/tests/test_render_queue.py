import unittest

from src.launcher.game.visual_editor.core.render_queue import (
    QueuedStageRender,
    StageRenderCoordinator,
)


class StageRenderCoordinatorTests(unittest.TestCase):
    def test_submit_debounces_to_latest_payload(self):
        queue = StageRenderCoordinator(debounce_seconds=0.3)
        queue.submit("first", now=0.0)
        latest = queue.submit("second", now=0.2)

        self.assertIsNone(queue.claim(now=0.49))
        self.assertEqual(queue.claim(now=0.5), QueuedStageRender(latest, "second"))

    def test_active_job_blocks_second_claim_and_old_result_is_stale(self):
        queue = StageRenderCoordinator(0.3)
        first = queue.submit("first", 0.0)
        self.assertEqual(queue.claim(0.3).generation, first)
        second = queue.submit("second", 0.4)

        self.assertIsNone(queue.claim(0.7))
        self.assertFalse(queue.complete(first))
        self.assertEqual(queue.claim(0.7).generation, second)

    def test_current_completion_is_accepted(self):
        queue = StageRenderCoordinator(0.3)
        generation = queue.submit("frame", 1.0)
        queue.claim(1.3)

        self.assertTrue(queue.complete(generation))
        self.assertFalse(queue.active)
        self.assertFalse(queue.has_pending)


if __name__ == "__main__":
    unittest.main()

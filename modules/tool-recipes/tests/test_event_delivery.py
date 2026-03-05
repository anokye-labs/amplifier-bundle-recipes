"""Tests for recipe event delivery fixes.

Verifies two bugs are fixed:
1. observability.events registration in mount() — so hooks-logging discovers recipe events
2. _show_progress uses await hooks.emit() instead of fire-and-forget asyncio.create_task
"""

import inspect
import re

from amplifier_module_tool_recipes.executor import RecipeExecutor


class TestShowProgressIsAsync:
    """Verify _show_progress is an async def (not sync def)."""

    def test_show_progress_is_async(self):
        """_show_progress must be async def so events are awaited, not fire-and-forget."""
        assert inspect.iscoroutinefunction(RecipeExecutor._show_progress), (
            "_show_progress must be async def, not sync def"
        )


class TestNoFireAndForgetEmit:
    """Verify no asyncio.create_task(hooks.emit(...)) pattern in executor source."""

    def test_no_fire_and_forget_emit_in_executor(self):
        """Source code must not contain create_task(hooks.emit pattern.

        The fire-and-forget pattern asyncio.create_task(hooks.emit(...)) causes
        events to be lost because they are scheduled but never awaited.
        The fix is to use 'await hooks.emit(...)' directly.
        """
        source_file = inspect.getfile(RecipeExecutor)
        with open(source_file) as f:
            source = f.read()

        # Check for the fire-and-forget anti-pattern
        pattern = r"create_task\s*\(\s*hooks\.emit"
        matches = re.findall(pattern, source)
        assert len(matches) == 0, (
            f"Found {len(matches)} fire-and-forget emit pattern(s) "
            f"(asyncio.create_task(hooks.emit(...))). "
            f"Use 'await hooks.emit(...)' instead."
        )

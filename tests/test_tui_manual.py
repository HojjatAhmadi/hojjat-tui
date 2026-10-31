"""Manual integration tests for the function form UI after priority fixes."""
import pytest

from hojjat_tui import builtin_functions
from hojjat_tui.tui import HojjatTUIApplication


@pytest.fixture(scope="module", autouse=True)
def ensure_builtins():
    builtin_functions.register_builtins()
    yield


def _wait(app, pilot):
    """Pause a few times to let async work settle."""


@pytest.mark.asyncio
async def test_function_form_execute_fills_params_and_runs():
    app = HojjatTUIApplication()
    async with app.run_test() as pilot:
        await pilot.pause(0.1)
        await pilot.pause(0.1)

        option_list = app.query_one("#function-list")
        names = [o.id for o in option_list._options]
        assert "factorial" in names, f"factorial not in {names}"

        option_list.index = names.index("factorial")
        await pilot.press("enter")
        await pilot.pause(0.2)

        n_input = app.query_one("#form-n")
        await pilot.click(n_input)
        await pilot.pause(0.1)
        await pilot.press("5")
        await pilot.pause(0.1)

        exec_btn = app.query_one("#execute-fn")
        await pilot.click(exec_btn)
        await pilot.pause(0.3)

        content = app.query_one("#content-area").renderable
        assert "120" in str(content), f"Expected 120 in result, got {content}"


@pytest.mark.asyncio
async def test_function_form_cancel_returns_to_prompt():
    app = HojjatTUIApplication()
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        option_list = app.query_one("#function-list")
        names = [o.id for o in option_list._options]
        if "factorial" not in names:
            pytest.skip("factorial not in registry")

        option_list.index = names.index("factorial")
        await pilot.press("enter")
        await pilot.pause(0.2)

        cancel_btn = app.query_one("#cancel-fn")
        await pilot.click(cancel_btn)
        await pilot.pause(0.2)

        content = app.query_one("#content-area").renderable
        assert "Select a function to execute" in str(content)


@pytest.mark.asyncio
async def test_error_demo_execution_shows_error_without_crash():
    app = HojjatTUIApplication()
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        option_list = app.query_one("#function-list")
        names = [o.id for o in option_list._options]
        if "error_demo" not in names:
            pytest.skip("error_demo not in registry")

        option_list.index = names.index("error_demo")
        await pilot.press("enter")
        await pilot.pause(0.2)

        msg_input = app.query_one("#form-message")
        await pilot.click(msg_input)
        await pilot.pause(0.1)
        # Type "TestFailure" (comma-separated keystrokes)
        await pilot.press("t", "e", "s", "t", "f", "a", "i", "l", "u", "r", "e")
        await pilot.pause(0.2)

        exec_btn = app.query_one("#execute-fn")
        await pilot.click(exec_btn)
        await pilot.pause(0.3)

        content = app.query_one("#content-area").renderable
        assert "Error" in str(content), f"Error not shown: {content}"

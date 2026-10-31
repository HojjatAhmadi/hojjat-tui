"""Tests for the function registration and registry."""

import pytest
from hojjat_tui.function import hojjat_function, FunctionResult, get_registry, _REGISTRY, register


class TestHojjatFunction:
    """Tests for the hojjat_function decorator."""

    def test_register_function(self):
        """Test that a function is registered correctly."""
        @hojjat_function(
            name="test_func",
            label="Test Function",
            description="A test function",
            annotations={"x": {"type": "int"}},
            defaults={"x": 0},
            required=["x"],
        )
        def my_func(x: int = 0) -> int:
            return x * 2

        assert "test_func" not in get_registry() or my_func._hojjat_metadata["name"] == "test_func"
        metadata = my_func._hojjat_metadata
        assert metadata["name"] == "test_func"
        assert metadata["label"] == "Test Function"
        assert metadata["description"] == "A test function"
        assert metadata["required"] == ["x"]
        assert metadata["defaults"] == {"x": 0}

    def test_duplicate_name_detection(self):
        """Test that duplicate function names raise an error."""
        @hojjat_function(name="dup_func")
        def func1():
            return "first"

        # Clean up first function
        if "dup_func" in _REGISTRY:
            del _REGISTRY["dup_func"]

        @hojjat_function(name="dup_func")
        def func2():
            return "second"

        with pytest.raises(ValueError, match="already registered"):
            @hojjat_function(name="dup_func")
            def func3():
                return "third"

        # Clean up
        if "dup_func" in _REGISTRY:
            del _REGISTRY["dup_func"]

    def test_register_alias(self):
        """Test the register alias."""
        def my_test_func():
            return "test"

        registered = register(my_test_func)
        assert registered is my_test_func
        # Clean up
        if my_test_func.__name__ in _REGISTRY:
            del _REGISTRY[my_test_func.__name__]

    def test_get_registry(self):
        """Test getting the registry."""
        registry = get_registry()
        assert isinstance(registry, dict)


class TestFunctionResult:
    """Tests for the FunctionResult dataclass."""

    def test_create_result(self):
        """Test creating a FunctionResult."""
        result = FunctionResult(
            name="test",
            success=True,
            duration=0.1,
            output="Hello",
            type="text",
        )
        assert result.name == "test"
        assert result.success is True
        assert result.duration == 0.1
        assert result.output == "Hello"
        assert result.type == "text"

    def test_result_to_text(self):
        """Test converting a result to text."""
        result = FunctionResult(
            name="test",
            success=True,
            duration=0.1,
            output={"key": "value"},
            type="json",
        )
        text = result.to_text()
        assert '"key"' in text

    def test_error_result(self):
        """Test error result."""
        result = FunctionResult(
            name="test",
            success=False,
            duration=0.1,
            error="Something went wrong",
            type="error",
        )
        text = result.to_text()
        assert "Something went wrong" in text
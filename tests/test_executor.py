"""Tests for the function executor."""

import pytest
from hojjat_tui.executor import execute_function
from hojjat_tui.function import _REGISTRY, _LOGGER, hojjat_function


class TestExecuteFunction:
    """Tests for the execute_function function."""

    def test_execute_success(self):
        """Test executing a successful function."""
        @hojjat_function(name="test_exec_success")
        def successful_func():
            return "success output"

        result = execute_function("test_exec_success")
        assert result.success is True
        assert result.output == "success output"
        assert result.error is None
        assert isinstance(result.duration, float)
        assert result.duration >= 0

        # Clean up
        if "test_exec_success" in _REGISTRY:
            del _REGISTRY["test_exec_success"]
        if "test_exec_success" in _LOGGER:
            del _LOGGER["test_exec_success"]

    def test_execute_with_kwargs(self):
        """Test executing a function with keyword arguments."""
        @hojjat_function(name="test_exec_kwargs")
        def kwargs_func(x: int = 0, y: int = 0):
            return x + y

        result = execute_function("test_exec_kwargs", kwargs={"x": 5, "y": 3})
        assert result.success is True
        assert result.output == 8

        # Clean up
        if "test_exec_kwargs" in _REGISTRY:
            del _REGISTRY["test_exec_kwargs"]
        if "test_exec_kwargs" in _LOGGER:
            del _LOGGER["test_exec_kwargs"]

    def test_execute_failure(self):
        """Test executing a function that raises an exception."""
        @hojjat_function(name="test_exec_fail")
        def failing_func():
            raise ValueError("Intentional error")

        result = execute_function("test_exec_fail")
        assert result.success is False
        assert "Intentional error" in result.error
        assert result.type == "error"
        assert "traceback" in result.metadata

        # Clean up
        if "test_exec_fail" in _REGISTRY:
            del _REGISTRY["test_exec_fail"]
        if "test_exec_fail" in _LOGGER:
            del _LOGGER["test_exec_fail"]

    def test_execute_unregistered(self):
        """Test executing an unregistered function."""
        result = execute_function("nonexistent_function")
        assert result.success is False
        assert "not registered" in result.error
        assert result.type == "error"

    def test_output_type_detection(self):
        """Test that output types are detected correctly."""
        # Test dict output
        @hojjat_function(name="test_dict_output")
        def dict_func():
            return {"key": "value"}

        result = execute_function("test_dict_output")
        assert result.type == "json"

        # Clean up
        if "test_dict_output" in _REGISTRY:
            del _REGISTRY["test_dict_output"]
        if "test_dict_output" in _LOGGER:
            del _LOGGER["test_dict_output"]

        # Test list output
        @hojjat_function(name="test_list_output")
        def list_func():
            return [{"a": 1}, {"b": 2}]

        result = execute_function("test_list_output")
        assert result.type == "table"

        # Clean up
        if "test_list_output" in _REGISTRY:
            del _REGISTRY["test_list_output"]
        if "test_list_output" in _LOGGER:
            del _LOGGER["test_list_output"]

    def test_execution_logging(self):
        """Test that executions are logged."""
        @hojjat_function(name="test_logging")
        def log_func():
            return "logged"

        execute_function("test_logging")
        assert "test_logging" in _LOGGER
        assert len(_LOGGER["test_logging"]) > 0

        # Clean up
        if "test_logging" in _REGISTRY:
            del _REGISTRY["test_logging"]
        if "test_logging" in _LOGGER:
            del _LOGGER["test_logging"]
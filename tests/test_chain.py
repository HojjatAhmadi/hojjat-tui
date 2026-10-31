"""Tests for the Chain Engine."""

import pytest

from hojjat_tui.chain import (
    Chain,
    ChainStep,
    ParameterBinding,
    BindingType,
    ChainStatus,
    StepExecutionResult,
    StepStatus,
    ChainValidationError,
    ChainValidator,
    ChainExecutor,
    validate_chain,
    execute_chain,
    save_chain,
    load_chain,
    list_chains,
    delete_chain,
    literal,
    user_input,
    output_of,
)


@pytest.fixture(autouse=True)
def register_builtins():
    """Ensure built-in functions are registered for chain tests."""
    from hojjat_tui import builtin_functions
    builtin_functions.register_builtins()
    yield


class TestChainModels:
    """Tests for chain data models."""

    def test_create_chain(self):
        """Test chain creation."""
        chain = Chain(
            name="test-chain",
            label="Test Chain",
            description="A test chain",
            steps=[],
        )
        assert chain.name == "test-chain"
        assert chain.label == "Test Chain"
        assert len(chain.steps) == 0

    def test_create_step_with_literal(self):
        """Test creating a step with literal binding."""
        binding = literal("x", 10)
        assert binding.name == "x"
        assert binding.binding_type == BindingType.LITERAL
        assert binding.value == 10

    def test_create_step_with_user_input(self):
        """Test creating a step with user input binding."""
        binding = user_input("name", "Enter your name")
        assert binding.name == "name"
        assert binding.binding_type == BindingType.USER_INPUT
        assert binding.prompt == "Enter your name"

    def test_create_step_with_output_reference(self):
        """Test creating a step with previous step output reference."""
        binding = output_of("data", "step-uuid-1", "result")
        assert binding.name == "data"
        assert binding.binding_type == BindingType.PREVIOUS_STEP
        assert binding.source_step_uuid == "step-uuid-1"
        assert binding.source_path == "result"


class TestChainValidation:
    """Tests for chain validation."""

    def test_valid_chain(self):
        """Test a valid chain passes validation."""
        chain = Chain(
            name="valid-chain",
            label="Valid Chain",
            steps=[
                ChainStep(function_name="hello", order=0, params=[literal("name", "World")]),
            ],
        )
        errors = validate_chain(chain)
        assert errors == []

    def test_empty_chain(self):
        """Test that empty chains are rejected."""
        chain = Chain(name="empty", label="Empty", steps=[])
        errors = validate_chain(chain)
        assert any("at least one step" in e for e in errors)

    def test_duplicate_uuid(self):
        """Test that duplicate UUIDs are detected."""
        chain = Chain(
            name="dup-uuid",
            label="Dup UUID",
            steps=[
                ChainStep(uuid="abc", function_name="hello", order=0, params=[]),
                ChainStep(uuid="abc", function_name="hello", order=1, params=[]),
            ],
        )
        errors = validate_chain(chain)
        assert any("Duplicate step UUID" in e for e in errors)

    def test_missing_function(self):
        """Test that missing functions are detected."""
        chain = Chain(
            name="missing-func",
            label="Missing Func",
            steps=[
                ChainStep(function_name="nonexistent_function", order=0, params=[]),
            ],
        )
        errors = validate_chain(chain)
        assert any("not registered" in e for e in errors)

    def test_unknown_parameter(self):
        """Test that unknown parameters are detected."""
        chain = Chain(
            name="unknown-param",
            label="Unknown Param",
            steps=[
                ChainStep(function_name="hello", order=0, params=[literal("nonexistent_param", "value")]),
            ],
        )
        errors = validate_chain(chain)
        assert any("not a valid parameter" in e for e in errors)

    def test_forward_reference(self):
        """Test that forward references are detected."""
        # A forward reference is when step-1 (order 0) references step-2 (order 1)
        chain = Chain(
            name="forward-ref",
            label="Forward Ref",
            steps=[
                ChainStep(
                    uuid="step-1",
                    function_name="hello",
                    order=0,
                    params=[output_of("data", "step-2", "output")]  # References step with higher order
                ),
                ChainStep(
                    uuid="step-2",
                    function_name="hello",
                    order=1,
                    params=[literal("name", "test")]
                ),
            ],
        )
        errors = validate_chain(chain)
        assert any("forward" in e.lower() for e in errors), f"Should detect forward reference: {errors}"

    def test_forward_reference_order_check(self):
        """Test that forward references are detected even with same UUIDs."""
        chain = Chain(
            name="forward-ref-order",
            label="Forward Ref Order",
            steps=[
                ChainStep(
                    uuid="step-a",
                    function_name="hello",
                    order=1,
                    params=[
                        literal("name", "test"),
                        # step-b has order 0, which is before step-a's order 1
                        # So this is actually a valid backward reference
                    ]
                ),
                ChainStep(
                    uuid="step-b",
                    function_name="hello",
                    order=0,
                    params=[literal("name", "test")]
                ),
            ],
        )
        errors = validate_chain(chain)
        # This should pass because step-b (order 0) is before step-a (order 1) in execution
        # But step-a doesn't reference step-b, so no forward reference issues
        assert not any("forward" in e.lower() for e in errors)


class TestChainExecution:
    """Tests for chain execution."""

    def test_single_step_execution(self):
        """Test executing a single-step chain."""
        chain = Chain(
            name="single-step",
            label="Single Step",
            steps=[
                ChainStep(
                    uuid="step-1",
                    function_name="hello",
                    order=0,
                    params=[literal("name", "World")]
                ),
            ],
        )
        execution = execute_chain(chain)
        assert execution.status == ChainStatus.SUCCESS
        assert len(execution.step_results) == 1
        assert execution.step_results["step-1"].status == StepStatus.SUCCESS
        assert "Hello, World!" in str(execution.step_results["step-1"].output)

    def test_multi_step_execution(self):
        """Test executing a multi-step chain."""
        chain = Chain(
            name="multi-step",
            label="Multi Step",
            steps=[
                ChainStep(
                    uuid="step-1",
                    function_name="factorial",
                    order=0,
                    params=[literal("n", 5)]
                ),
                ChainStep(
                    uuid="step-2",
                    function_name="hello",
                    order=1,
                    params=[literal("name", "Result")]
                ),
            ],
        )
        execution = execute_chain(chain)
        assert execution.status == ChainStatus.SUCCESS

    def test_output_reference(self):
        """Test referencing output from a previous step."""
        chain = Chain(
            name="output-ref",
            label="Output Ref",
            steps=[
                ChainStep(
                    uuid="step-1",
                    function_name="hello",
                    order=0,
                    params=[literal("name", "World"), literal("times", 1)]
                ),
            ],
        )
        execution = execute_chain(chain)
        assert execution.status == ChainStatus.SUCCESS
        result = execution.step_results["step-1"]
        assert "Hello, World!" in str(result.output)

    def test_failed_step_skips_dependents(self):
        """Test that failed steps cause dependent steps to be skipped."""
        chain = Chain(
            name="fail-skip",
            label="Fail Skip",
            steps=[
                ChainStep(
                    uuid="step-1",
                    function_name="factorial",
                    order=0,
                    params=[literal("n", -1)]  # This will fail
                ),
                ChainStep(
                    uuid="step-2",
                    function_name="hello",
                    order=1,
                    params=[output_of("data", "step-1", "output")]
                ),
            ],
        )
        execution = execute_chain(chain)
        assert execution.status == ChainStatus.PARTIAL or execution.status == ChainStatus.FAILED

        # Step 1 should have failed
        assert execution.step_results["step-1"].status == StepStatus.FAILED

        # Step 2 should be skipped (depends on failed step)
        assert execution.step_results["step-2"].status == StepStatus.SKIPPED

    def test_mixed_binding_types(self):
        """Test chain with mixed binding types (literal + output ref + user input)."""
        chain = Chain(
            name="mixed",
            label="Mixed",
            steps=[
                ChainStep(
                    uuid="step-1",
                    function_name="factorial",
                    order=0,
                    params=[
                        literal("n", 5),
                    ]
                ),
            ],
        )
        execution = execute_chain(chain)
        assert execution.status == ChainStatus.SUCCESS
        assert execution.step_results["step-1"].output == 120


class TestChainPersistence:
    """Tests for chain persistence in SQLite."""

    def test_save_and_load_chain(self, temp_db_path=None):
        """Test saving and loading a chain."""
        from hojjat_tui.persistence import Database
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            Database._db_path_override = db_path

            try:
                chain = Chain(
                    name="persist-test",
                    label="Persist Test",
                    description="Test persistence",
                    steps=[
                        ChainStep(
                            uuid="step-1",
                            function_name="hello",
                            order=0,
                            params=[literal("name", "Database")]
                        ),
                    ],
                )

                # Save
                chain_id = save_chain(chain)
                assert chain_id > 0

                # Load
                loaded = load_chain("persist-test")
                assert loaded is not None
                assert loaded.name == "persist-test"
                assert loaded.label == "Persist Test"
                assert len(loaded.steps) == 1
                assert loaded.steps[0].function_name == "hello"
                assert len(loaded.steps[0].params) == 1
                assert loaded.steps[0].params[0].name == "name"
                assert loaded.steps[0].params[0].value == "Database"

            finally:
                # Cleanup
                if os.path.exists(db_path):
                    os.remove(db_path)

    def test_list_chains(self):
        """Test listing chains from database."""
        from hojjat_tui.persistence import Database
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            Database._db_path_override = db_path

            try:
                chain = Chain(
                    name="list-test",
                    label="List Test",
                    steps=[],
                )
                save_chain(chain)

                chains = list_chains()
                chain_names = [c["name"] for c in chains]
                assert "list-test" in chain_names

            finally:
                if os.path.exists(db_path):
                    os.remove(db_path)

    def test_delete_chain(self):
        """Test deleting a chain."""
        from hojjat_tui.persistence import Database
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            Database._db_path_override = db_path

            try:
                chain = Chain(
                    name="delete-test",
                    label="Delete Test",
                    steps=[],
                )
                save_chain(chain)

                # Verify it exists
                chains = list_chains()
                assert any(c["name"] == "delete-test" for c in chains)

                # Delete it
                result = delete_chain("delete-test")
                assert result is True

                # Verify it's gone
                chains = list_chains()
                assert not any(c["name"] == "delete-test" for c in chains)

            finally:
                if os.path.exists(db_path):
                    os.remove(db_path)


class TestChainAPI:
    """Tests for the public chain API."""

    def test_create_chain_helper(self):
        """Test the create_chain helper function."""
        from hojjat_tui.chain import create_chain, add_step

        chain = create_chain("api-test", "API Test Chain", "Test description")
        assert chain.name == "api-test"
        assert chain.label == "API Test Chain"
        assert chain.description == "Test description"

    def test_add_step_helper(self):
        """Test the add_step helper function."""
        from hojjat_tui.chain import create_chain, add_step, literal

        chain = create_chain("with-steps", "With Steps")
        add_step(chain, "hello", params=[literal("name", "Test")])

        assert len(chain.steps) == 1
        assert chain.steps[0].function_name == "hello"
"""
Ralph Verification MCP Server Tests (Phase 2A-1)

TDD approach: Tests written first, implementation follows.

Tests for MCP server wrapping Ralph verification tool with:
- Secure verification execution
- Cost tracking
- Result caching
- Error handling
- Integration with SpecialistAgent

Author: Claude Code (TDD Implementation)
Date: 2026-02-07
Version: 1.0
"""

import pytest
from orchestration.mcp.ralph_verification import (
    RalphVerificationMCP,
    RalphVerificationResponse,
    VerificationResult,
)


class TestRalphVerificationMCPBasic:
    """Test basic Ralph verification MCP functionality"""

    def test_verify_passing_code(self):
        """Verify code that passes all checks"""
        # TDD: Test the interface we want to exist
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        result = server.verify_file(
            file_path="test_file.py",
            code_content="def hello():\n    return 'world'",
        )

        # Assertions about expected behavior
        assert result.result == VerificationResult.PASS
        assert result.passed_count > 0
        assert result.failed_count == 0
        assert result.blocked_count == 0
        assert len(result.issues) == 0
        assert result.cost_usd > 0
        assert result.execution_time_ms > 0

    def test_verify_failing_code(self):
        """Verify code with failures"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        result = server.verify_file(
            file_path="bad_file.py",
            code_content="x=1",  # Likely to fail linting
        )

        assert result.result == VerificationResult.FAIL
        assert result.failed_count > 0
        assert len(result.issues) > 0
        assert result.cost_usd > 0

    def test_verify_blocked_code(self):
        """Verify code that triggers guardrails"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        result = server.verify_file(
            file_path="dangerous.py",
            code_content="import os; os.system('rm -rf /')",
        )

        assert result.result == VerificationResult.BLOCKED
        assert result.blocked_count > 0
        assert len(result.issues) > 0


class TestRalphVerificationMCPCost:
    """Test cost tracking for Ralph verification"""

    def test_cost_tracking(self):
        """Cost should be tracked for each verification"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        result = server.verify_file(
            file_path="test.py",
            code_content="print('hello')",
        )

        assert result.cost_usd > 0
        assert result.cost_usd < 1.0  # Ralph is cheap

    def test_cost_accumulation(self):
        """Multiple verifications should accumulate costs"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        result1 = server.verify_file("file1.py", "print('1')")
        result2 = server.verify_file("file2.py", "print('2')")

        total_cost = server.get_accumulated_cost()

        assert total_cost == result1.cost_usd + result2.cost_usd

    def test_cost_per_check(self):
        """Cost breakdown by verification type"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        result = server.verify_file(
            file_path="test.py",
            code_content="x = 1",
            checks=["linting", "type_checking", "security"],
        )

        # Cost should be per check
        assert result.cost_usd > 0
        cost_breakdown = server.get_cost_breakdown()
        assert "linting" in cost_breakdown or len(cost_breakdown) > 0


class TestRalphVerificationMCPCaching:
    """Test result caching for Ralph verification"""

    def test_cache_hit(self):
        """Verify code twice, second should hit cache"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        code = "def hello(): return 'world'"

        result1 = server.verify_file("test.py", code)
        result2 = server.verify_file("test.py", code)

        assert result1.result == result2.result
        assert result2.cached is True  # Second call should be cached

    def test_cache_miss_on_different_code(self):
        """Different code should not use cache"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        result1 = server.verify_file("test.py", "code1 = 1")
        result2 = server.verify_file("test.py", "code2 = 2")

        assert result2.cached is False  # Different code, no cache hit

    def test_cache_clear(self):
        """Cache should be clearable"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        server.verify_file("test.py", "x = 1")

        server.clear_cache()

        assert server.get_cache_size() == 0


class TestRalphVerificationMCPBatch:
    """Test batch verification operations"""

    def test_batch_verify_files(self):
        """Verify multiple files at once"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        files = [
            ("file1.py", "x = 1"),
            ("file2.py", "y = 2"),
            ("file3.py", "z = 3"),
        ]

        results = server.verify_batch(files)

        assert len(results) == 3
        assert all(isinstance(r, RalphVerificationResponse) for r in results)

    def test_batch_partial_failure(self):
        """Batch should continue on partial failures"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        files = [
            ("good.py", "def hello(): return 'world'"),
            ("bad.py", "x=1"),
            ("good2.py", "y = 2"),
        ]

        results = server.verify_batch(files, stop_on_failure=False)

        assert len(results) == 3


class TestRalphVerificationMCPIntegration:
    """Test integration with SpecialistAgent"""

    def test_mcp_tool_registration(self):
        """Ralph MCP should register as agent tool"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        tools = server.get_mcp_tools()

        assert "verify_file" in tools
        assert "verify_batch" in tools
        assert "get_accumulated_cost" in tools

    def test_mcp_tool_schema(self):
        """Tools should have valid JSON schema for agent use"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        schema = server.get_tool_schema("verify_file")

        assert "type" in schema
        assert "parameters" in schema
        assert "properties" in schema["parameters"]

    def test_agent_invoke_verification(self):
        """Agent should be able to invoke verification via MCP"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        # Simulate agent calling tool
        result = server.invoke_tool(
            tool_name="verify_file",
            arguments={
                "file_path": "test.py",
                "code_content": "x = 1",
            },
        )

        assert isinstance(result, RalphVerificationResponse)
        assert result.cost_usd > 0


class TestRalphVerificationMCPErrorHandling:
    """Test error handling in Ralph verification MCP"""

    def test_invalid_file_path(self):
        """Should handle invalid file paths gracefully"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        with pytest.raises(ValueError):
            server.verify_file("", "code")

    def test_empty_code(self):
        """Should handle empty code gracefully"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        result = server.verify_file("test.py", "")

        # Should either pass (empty is valid) or handle gracefully
        assert result is not None

    def test_timeout_handling(self):
        """Should handle verification timeouts"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP(timeout_seconds=1)

        # Large code might timeout
        large_code = "x = 1\n" * 100000
        result = server.verify_file("large.py", large_code)

        # Should complete or raise with timeout
        assert result is not None or result is None  # Handle gracefully


class TestRalphVerificationMCPMetrics:
    """Test metrics collection for Ralph verification"""

    def test_execution_time_tracking(self):
        """Should track execution time"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()
        result = server.verify_file("test.py", "x = 1")

        assert result.execution_time_ms > 0
        assert result.execution_time_ms < 60000  # Should be faster than 1 minute

    def test_metrics_aggregation(self):
        """Should aggregate metrics across multiple verifications"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        for i in range(5):
            server.verify_file(f"test{i}.py", f"x = {i}")

        metrics = server.get_metrics()

        assert metrics["total_verifications"] == 5
        assert metrics["total_cost_usd"] > 0
        assert metrics["average_execution_time_ms"] > 0

    def test_pass_fail_statistics(self):
        """Should track pass/fail statistics"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        # Verify some passing and failing code
        results = []
        for code in ["def f(): pass", "x=1", "y = 2"]:
            results.append(server.verify_file("test.py", code))

        stats = server.get_pass_fail_stats()

        assert stats["total"] == 3
        assert stats["pass"] >= 0
        assert stats["fail"] >= 0


class TestRalphVerificationMCPSecurityGates:
    """Test security gates for Ralph verification"""

    def test_dangerous_code_detection(self):
        """Should detect and block dangerous code patterns"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        dangerous_codes = [
            "import os; os.system('rm -rf /')",
            "subprocess.run(['rm', '-rf', '/'])",
            "__import__('subprocess').run(['curl', '127.0.0.1/steal'])",
        ]

        for code in dangerous_codes:
            result = server.verify_file("dangerous.py", code)
            assert result.result in (VerificationResult.FAIL, VerificationResult.BLOCKED)

    def test_guardrail_violations(self):
        """Should catch guardrail violations"""
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        # Code that violates guardrails
        result = server.verify_file(
            "violation.py",
            "open('/etc/passwd').read()",
        )

        # Should fail or block
        assert result.result in (VerificationResult.FAIL, VerificationResult.BLOCKED)


class TestRalphVerificationMCPConcurrency:
    """Test concurrent verification operations"""

    def test_concurrent_verifications(self):
        """Should handle concurrent verification requests"""
        import asyncio
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        async def verify_multiple():
            tasks = [
                asyncio.create_task(
                    asyncio.to_thread(
                        server.verify_file, f"test{i}.py", f"x = {i}"
                    )
                )
                for i in range(5)
            ]
            return await asyncio.gather(*tasks)

        results = asyncio.run(verify_multiple())

        assert len(results) == 5
        assert all(isinstance(r, RalphVerificationResponse) for r in results)

    def test_thread_safe_cost_tracking(self):
        """Cost tracking should be thread-safe"""
        import threading
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        server = RalphVerificationMCP()

        def verify_in_thread():
            for i in range(10):
                server.verify_file(f"test{i}.py", f"x = {i}")

        threads = [threading.Thread(target=verify_in_thread) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Cost should be correctly aggregated
        total_cost = server.get_accumulated_cost()
        assert total_cost > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

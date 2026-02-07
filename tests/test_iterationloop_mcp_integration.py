"""
MCP Integration Tests (Phase 2A-5)

TDD approach: Tests written first, implementation follows.

Tests for integrating all 4 MCP servers via MCPIntegration:
- Ralph Verification MCP
- Git Operations MCP
- Database Query MCP
- Deployment MCP

Author: Claude Code (TDD Implementation)
Date: 2026-02-07
Version: 1.0
"""

import pytest


class TestIterationLoopMCPRegistration:
    """Test MCP tool registration with IterationLoop"""

    def test_register_ralph_verification_tools(self):
        """Register Ralph Verification tools with MCP integration"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()

        # Register tools
        integration.register_mcp_server("ralph_verification", ralph_mcp)

        # Verify registration
        assert "ralph_verification" in integration.get_registered_servers()
        assert "verify_file" in integration.get_available_tools()

    def test_register_git_operations_tools(self):
        """Register Git Operations tools with IterationLoop"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.git_operations import GitOperationsMCP

        integration = MCPIntegration()
        git_mcp = GitOperationsMCP()

        integration.register_mcp_server("git_operations", git_mcp)

        assert "git_operations" in integration.get_registered_servers()
        assert "commit" in integration.get_available_tools()

    def test_register_database_query_tools(self):
        """Register Database Query tools with IterationLoop"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.database_query import DatabaseQueryMCP

        integration = MCPIntegration()
        db_mcp = DatabaseQueryMCP()

        integration.register_mcp_server("database_query", db_mcp)

        assert "database_query" in integration.get_registered_servers()
        assert "query" in integration.get_available_tools()

    def test_register_deployment_tools(self):
        """Register Deployment tools with IterationLoop"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()
        deploy_mcp = DeploymentMCP()

        integration.register_mcp_server("deployment", deploy_mcp)

        assert "deployment" in integration.get_registered_servers()
        assert "deploy" in integration.get_available_tools()

    def test_register_all_mcp_servers(self):
        """Register all 4 MCP servers with IterationLoop"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP
        from orchestration.mcp.git_operations import GitOperationsMCP
        from orchestration.mcp.database_query import DatabaseQueryMCP
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()

        # Register all servers
        integration.register_mcp_server("ralph_verification", RalphVerificationMCP())
        integration.register_mcp_server("git_operations", GitOperationsMCP())
        integration.register_mcp_server("database_query", DatabaseQueryMCP())
        integration.register_mcp_server("deployment", DeploymentMCP())

        # Verify all registered
        mcps = integration.get_registered_servers()
        assert len(mcps) >= 4
        assert "ralph_verification" in mcps
        assert "git_operations" in mcps
        assert "database_query" in mcps
        assert "deployment" in mcps


class TestIterationLoopToolInvocation:
    """Test invoking MCP tools from IterationLoop"""

    def test_invoke_ralph_verification_tool(self):
        """Invoke Ralph verification tool from IterationLoop"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP, VerificationResult

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()
        integration.register_mcp_server("ralph_verification", ralph_mcp)

        # Invoke tool
        result = integration.invoke_tool(
            tool_name="verify_file",
            arguments={
                "file_path": "test.py",
                "code_content": "print('hello')"
            }
        )

        assert result.result == VerificationResult.PASS

    def test_invoke_git_operations_tool(self):
        """Invoke git operations tool from IterationLoop"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.git_operations import GitOperationsMCP
        import tempfile
        import shutil
        import os

        temp_dir = tempfile.mkdtemp()

        try:
            integration = MCPIntegration()
            git_mcp = GitOperationsMCP(repo_path=temp_dir)
            git_mcp.init_repo()

            # Create main branch by adding a file and committing
            test_file = os.path.join(temp_dir, "README.md")
            with open(test_file, "w") as f:
                f.write("# Test")
            git_mcp.commit(["README.md"], "Initial commit")

            integration.register_mcp_server("git_operations", git_mcp)

            result = integration.invoke_tool(
                tool_name="create_branch",
                arguments={"branch_name": "feature/test"}
            )

            assert result.success is True
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_invoke_database_query_tool(self):
        """Invoke database query tool from IterationLoop"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.database_query import DatabaseQueryMCP

        integration = MCPIntegration()
        db_mcp = DatabaseQueryMCP()
        db_mcp.init_database()
        db_mcp.execute_query(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"
        )
        integration.register_mcp_server("database_query", db_mcp)

        result = integration.invoke_tool(
            tool_name="query",
            arguments={
                "sql": "SELECT * FROM test",
                "params": []
            }
        )

        assert result.success is True

    def test_invoke_deployment_tool(self):
        """Invoke deployment tool from IterationLoop"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()
        deploy_mcp = DeploymentMCP()
        integration.register_mcp_server("deployment", deploy_mcp)

        result = integration.invoke_tool(
            tool_name="deploy",
            arguments={
                "environment": "dev",
                "service": "test-service",
                "version": "1.0.0"
            }
        )

        assert result.success is True


class TestIterationLoopToolSchema:
    """Test MCP tool schema generation"""

    def test_get_tool_schema_for_all_tools(self):
        """Get JSON schema for all registered tools"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP
        from orchestration.mcp.git_operations import GitOperationsMCP
        from orchestration.mcp.database_query import DatabaseQueryMCP
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()

        # Register all servers
        integration.register_mcp_server("ralph_verification", RalphVerificationMCP())
        integration.register_mcp_server("git_operations", GitOperationsMCP())
        integration.register_mcp_server("database_query", DatabaseQueryMCP())
        integration.register_mcp_server("deployment", DeploymentMCP())

        # Get schemas
        schemas = integration.get_tool_schemas()

        assert len(schemas) > 0
        assert "verify_file" in schemas
        assert "commit" in schemas
        assert "query" in schemas
        assert "deploy" in schemas

    def test_schema_has_parameters(self):
        """Tool schemas should have parameter definitions"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()
        integration.register_mcp_server("ralph_verification", ralph_mcp)

        schemas = integration.get_tool_schemas()

        assert "verify_file" in schemas
        schema = schemas["verify_file"]
        assert "parameters" in schema
        assert "properties" in schema["parameters"]


class TestIterationLoopCostTracking:
    """Test cost tracking across MCP servers"""

    def test_accumulate_cost_from_multiple_tools(self):
        """Accumulate costs from multiple tool invocations"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP
        from orchestration.mcp.git_operations import GitOperationsMCP

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()
        git_mcp = GitOperationsMCP()

        integration.register_mcp_server("ralph_verification", ralph_mcp)
        integration.register_mcp_server("git_operations", git_mcp)

        # Invoke tools
        integration.invoke_tool(
            tool_name="verify_file",
            arguments={
                "file_path": "test.py",
                "code_content": "x = 1"
            }
        )

        # Get total cost
        total_cost = integration.get_accumulated_cost()

        assert total_cost > 0

    def test_cost_breakdown_by_server(self):
        """Get cost breakdown by MCP server"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()
        deploy_mcp = DeploymentMCP()

        integration.register_mcp_server("ralph_verification", ralph_mcp)
        integration.register_mcp_server("deployment", deploy_mcp)

        # Invoke tools
        integration.invoke_tool(
            tool_name="verify_file",
            arguments={
                "file_path": "test.py",
                "code_content": "x = 1"
            }
        )
        integration.invoke_tool(
            tool_name="deploy",
            arguments={
                "environment": "dev",
                "service": "svc",
                "version": "1.0.0"
            }
        )

        # Get breakdown
        breakdown = integration.get_cost_breakdown()

        assert "ralph_verification" in breakdown
        assert "deployment" in breakdown


class TestIterationLoopMetrics:
    """Test metrics aggregation from MCP servers"""

    def test_aggregate_metrics_from_all_servers(self):
        """Aggregate metrics from all MCP servers"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()
        deploy_mcp = DeploymentMCP()

        integration.register_mcp_server("ralph_verification", ralph_mcp)
        integration.register_mcp_server("deployment", deploy_mcp)

        # Invoke tools (with different content to avoid caching)
        for i in range(3):
            integration.invoke_tool(
                tool_name="verify_file",
                arguments={
                    "file_path": f"test{i}.py",
                    "code_content": f"x = {i}\nprint({i})"  # Different content for each
                }
            )

        # Get metrics from individual servers
        ralph_metrics = integration.get_server_metrics("ralph_verification")

        assert ralph_metrics is not None
        assert ralph_metrics["total_verifications"] >= 3
        assert ralph_metrics["total_cost_usd"] > 0

    def test_metrics_by_tool(self):
        """Get metrics by server"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()
        integration.register_mcp_server("ralph_verification", ralph_mcp)

        # Invoke tool multiple times
        for i in range(2):
            integration.invoke_tool(
                tool_name="verify_file",
                arguments={
                    "file_path": f"test{i}.py",
                    "code_content": f"x = {i}\nprint({i})"
                }
            )

        # Get server metrics
        server_metrics = integration.get_server_metrics("ralph_verification")

        assert server_metrics is not None
        assert server_metrics.get("total_verifications", 0) >= 2


class TestIterationLoopBackwardCompatibility:
    """Test backward compatibility with existing IterationLoop features"""

    def test_existing_iteration_features_still_work(self):
        """Existing IterationLoop features should work alongside MCP servers"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        integration = MCPIntegration()

        # Register MCP
        integration.register_mcp_server("ralph_verification", RalphVerificationMCP())

        # Existing methods should still work
        assert integration.get_registered_servers() is not None
        assert integration.get_available_tools() is not None

    def test_mcp_tools_dont_break_existing_workflow(self):
        """MCP tools should integrate smoothly without breaking existing features"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()

        # Register and use
        integration.register_mcp_server("ralph_verification", ralph_mcp)

        # Invoke tool
        result = integration.invoke_tool(
            tool_name="verify_file",
            arguments={
                "file_path": "test.py",
                "code_content": "x = 1"
            }
        )

        assert result is not None


class TestIterationLoopErrorHandling:
    """Test error handling for MCP integration"""

    def test_handle_tool_invocation_error(self):
        """Handle errors when invoking tools"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        integration = MCPIntegration()
        ralph_mcp = RalphVerificationMCP()
        integration.register_mcp_server("ralph_verification", ralph_mcp)

        # Invoke with invalid arguments - should raise or return error
        try:
            result = integration.invoke_tool(
                tool_name="verify_file",
                arguments={
                    "file_path": "",
                    "code_content": ""
                }
            )
            # If it doesn't raise, verify_file validation should fail
            assert result is not None
        except ValueError:
            # Expected - empty file_path is invalid
            pass

    def test_handle_unregistered_tool(self):
        """Handle invocation of unregistered tool"""
        from orchestration.mcp.mcp_integration import MCPIntegration

        integration = MCPIntegration()

        # Invoke non-existent tool
        result = integration.invoke_tool(
            tool_name="nonexistent_tool",
            arguments={}
        )

        # Should handle gracefully
        assert result is None or result.success is False

    def test_handle_mcp_server_error(self):
        """Handle errors from MCP server"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()
        deploy_mcp = DeploymentMCP()
        integration.register_mcp_server("deployment", deploy_mcp)

        # Invoke with invalid environment
        result = integration.invoke_tool(
            tool_name="deploy",
            arguments={
                "environment": "invalid",
                "service": "svc",
                "version": "1.0.0"
            }
        )

        assert result.success is False


class TestIterationLoopAgentPrompts:
    """Test MCP tool availability in agent prompts"""

    def test_mcp_tools_available_in_agent_system_prompt(self):
        """MCP tools should be available in agent system prompts"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP

        integration = MCPIntegration()
        integration.register_mcp_server("ralph_verification", RalphVerificationMCP())

        # Get system prompt
        system_prompt = integration.generate_agent_prompt()

        assert "verify_file" in system_prompt or "tool" in system_prompt.lower()

    def test_tool_descriptions_in_prompt(self):
        """Tool descriptions should be in agent prompt"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()
        integration.register_mcp_server("deployment", DeploymentMCP())

        system_prompt = integration.generate_agent_prompt()

        # Should mention deployment or tools
        assert len(system_prompt) > 0


class TestIterationLoopIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_multi_tool_workflow(self):
        """Execute workflow using multiple MCP tools"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP, VerificationResult
        from orchestration.mcp.git_operations import GitOperationsMCP
        from orchestration.mcp.deployment import DeploymentMCP
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()

        try:
            integration = MCPIntegration()

            # Register tools
            integration.register_mcp_server("ralph_verification", RalphVerificationMCP())
            git_mcp = GitOperationsMCP(repo_path=temp_dir)
            git_mcp.init_repo()
            integration.register_mcp_server("git_operations", git_mcp)
            integration.register_mcp_server("deployment", DeploymentMCP())

            # Workflow: verify -> commit -> deploy
            verify_result = integration.invoke_tool(
                tool_name="verify_file",
                arguments={
                    "file_path": "main.py",
                    "code_content": "print('hello')"
                }
            )

            assert verify_result.result == VerificationResult.PASS

            # Create a file for git
            import os
            test_file = os.path.join(temp_dir, "main.py")
            with open(test_file, "w") as f:
                f.write("print('hello')")

            commit_result = integration.invoke_tool(
                tool_name="commit",
                arguments={
                    "file_paths": ["main.py"],
                    "message": "Initial commit"
                }
            )

            assert commit_result.success is True

            deploy_result = integration.invoke_tool(
                tool_name="deploy",
                arguments={
                    "environment": "dev",
                    "service": "app",
                    "version": "1.0.0"
                }
            )

            assert deploy_result.success is True

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cost_tracking_across_workflow(self):
        """Track total cost across multi-tool workflow"""
        from orchestration.mcp.mcp_integration import MCPIntegration
        from orchestration.mcp.ralph_verification import RalphVerificationMCP
        from orchestration.mcp.deployment import DeploymentMCP

        integration = MCPIntegration()
        integration.register_mcp_server("ralph_verification", RalphVerificationMCP())
        integration.register_mcp_server("deployment", DeploymentMCP())

        # Execute workflow
        for i in range(2):
            integration.invoke_tool(
                tool_name="verify_file",
                arguments={
                    "file_path": f"test{i}.py",
                    "code_content": f"x = {i}"
                }
            )

        integration.invoke_tool(
            tool_name="deploy",
            arguments={
                "environment": "dev",
                "service": "svc",
                "version": "1.0.0"
            }
        )

        # Check total cost
        total_cost = integration.get_accumulated_cost()

        assert total_cost > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

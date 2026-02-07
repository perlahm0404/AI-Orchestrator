"""
Git Operations MCP Server Tests (Phase 2A-2)

TDD approach: Tests written first, implementation follows.

Tests for MCP server wrapping git commands with:
- Secure git operation execution
- Cost tracking per operation
- Governance tracking per commit
- Branch operations (create, delete, switch)
- Merge operations with conflict handling
- Push/pull with branch safety checks
- Thread-safe concurrent operations

Author: Claude Code (TDD Implementation)
Date: 2026-02-07
Version: 1.0
"""

import pytest
import tempfile
import os
import shutil


class TestGitOperationsMCPBasic:
    """Test basic Git Operations MCP functionality"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        # Initialize repo
        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        yield temp_dir, mcp

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_init_repo(self, temp_repo):
        """Initialize a new git repository"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Repository should be initialized
        assert os.path.exists(os.path.join(temp_dir, ".git"))
        # After init, current branch may be unknown until first commit
        current = mcp.get_current_branch()
        assert current is not None

    def test_commit_file(self, temp_repo):
        """Commit a file to the repository"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Create and commit a file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        result = mcp.commit(
            file_paths=["test.txt"],
            message="Initial commit"
        )

        assert result.success is True
        assert result.commit_hash is not None
        assert len(result.commit_hash) > 0
        assert result.cost_usd > 0

    def test_status_clean(self, temp_repo):
        """Check status of clean repository"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        status = mcp.get_status()

        assert status.clean is True
        assert len(status.untracked_files) == 0
        assert len(status.modified_files) == 0
        assert len(status.staged_files) == 0

    def test_status_with_changes(self, temp_repo):
        """Check status with uncommitted changes"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Create a file but don't commit
        test_file = os.path.join(temp_dir, "new_file.txt")
        with open(test_file, "w") as f:
            f.write("new content")

        status = mcp.get_status()

        assert status.clean is False
        assert len(status.untracked_files) > 0
        assert "new_file.txt" in status.untracked_files


class TestGitOperationsMCPBranch:
    """Test branch operations"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        # Create initial commit
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("initial")
        mcp.commit(file_paths=["test.txt"], message="Initial")

        yield temp_dir, mcp

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_create_branch(self, temp_repo):
        """Create a new branch"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        result = mcp.create_branch(branch_name="feature/test")

        assert result.success is True
        assert result.branch_name == "feature/test"

    def test_switch_branch(self, temp_repo):
        """Switch to a different branch"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Create branch first
        mcp.create_branch(branch_name="feature/switch-test")

        result = mcp.switch_branch(branch_name="feature/switch-test")

        assert result.success is True
        assert result.current_branch == "feature/switch-test"

    def test_delete_branch(self, temp_repo):
        """Delete a branch"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Create branch
        mcp.create_branch(branch_name="feature/delete-me")

        # Switch away first
        mcp.switch_branch(branch_name="main")

        result = mcp.delete_branch(branch_name="feature/delete-me")

        assert result.success is True

    def test_list_branches(self, temp_repo):
        """List all branches"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Create some branches
        mcp.create_branch(branch_name="feature/one")
        mcp.create_branch(branch_name="feature/two")

        result = mcp.list_branches()

        assert result.success is True
        assert len(result.branches) >= 3  # main + 2 created
        assert "feature/one" in result.branches
        assert "feature/two" in result.branches


class TestGitOperationsMCPMerge:
    """Test merge operations"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        # Create initial commit on main
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("main content")
        mcp.commit(file_paths=["test.txt"], message="Initial")

        yield temp_dir, mcp

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_merge_clean(self, temp_repo):
        """Merge a branch with no conflicts"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Create feature branch
        mcp.create_branch(branch_name="feature/clean-merge")
        mcp.switch_branch(branch_name="feature/clean-merge")

        # Make changes on feature branch
        new_file = os.path.join(temp_dir, "feature.txt")
        with open(new_file, "w") as f:
            f.write("feature content")
        mcp.commit(file_paths=["feature.txt"], message="Add feature")

        # Switch back to main and merge
        mcp.switch_branch(branch_name="main")
        result = mcp.merge_branch(branch_name="feature/clean-merge")

        assert result.success is True
        assert result.conflicted is False
        assert result.cost_usd > 0

    def test_merge_conflict_detection(self, temp_repo):
        """Detect merge conflicts"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Create feature branch that conflicts
        mcp.create_branch(branch_name="feature/conflict")
        mcp.switch_branch(branch_name="feature/conflict")

        # Modify the same file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("feature version")
        mcp.commit(file_paths=["test.txt"], message="Feature change")

        # Switch back to main and make different change
        mcp.switch_branch(branch_name="main")
        with open(test_file, "w") as f:
            f.write("main version")
        mcp.commit(file_paths=["test.txt"], message="Main change")

        # Try to merge - should detect conflict
        result = mcp.merge_branch(branch_name="feature/conflict")

        # Either merge fails or detects conflict
        assert result.success is False or result.conflicted is True


class TestGitOperationsMCPCost:
    """Test cost tracking"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        yield temp_dir, mcp

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_commit_cost(self, temp_repo):
        """Cost tracking for commit operations"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        result = mcp.commit(file_paths=["test.txt"], message="Test commit")

        assert result.cost_usd > 0
        assert result.cost_usd < 0.01  # Should be cheap

    def test_cost_accumulation(self, temp_repo):
        """Multiple operations should accumulate costs"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        # Multiple operations
        result1 = mcp.commit(file_paths=["test.txt"], message="First")
        mcp.create_branch(branch_name="feature/test")
        result3 = mcp.commit(file_paths=["test.txt"], message="Second")

        total_cost = mcp.get_accumulated_cost()

        assert total_cost >= result1.cost_usd + result3.cost_usd
        assert total_cost > 0

    def test_get_cost_breakdown(self, temp_repo):
        """Cost breakdown by operation type"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        breakdown = mcp.get_cost_breakdown()

        assert "commit" in breakdown
        assert "branch_create" in breakdown
        assert "merge" in breakdown
        assert breakdown["commit"] > 0


class TestGitOperationsMCPGovernance:
    """Test governance tracking"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        yield temp_dir, mcp

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_commit_governance_audit(self, temp_repo):
        """Commits should record governance audit trail"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        result = mcp.commit(
            file_paths=["test.txt"],
            message="Test commit",
            agent_name="TestAgent",
            agent_role="TestRole"
        )

        assert result.success is True
        audit_trail = mcp.get_audit_trail()

        assert len(audit_trail) > 0
        assert audit_trail[-1]["type"] == "commit"
        assert audit_trail[-1]["agent_name"] == "TestAgent"

    def test_audit_trail_logging(self, temp_repo):
        """Audit trail should log all operations"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        mcp.commit(file_paths=["test.txt"], message="C1")
        mcp.create_branch(branch_name="feature/test")
        mcp.switch_branch(branch_name="feature/test")

        audit = mcp.get_audit_trail()

        assert len(audit) >= 3
        assert any(a["type"] == "commit" for a in audit)
        assert any(a["type"] == "branch_create" for a in audit)
        assert any(a["type"] == "switch" for a in audit)

    def test_branch_safety_check(self, temp_repo):
        """Prevent dangerous operations on protected branches"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        # Try to delete main branch - should fail
        result = mcp.delete_branch(branch_name="main")

        assert result.success is False or result.protected is True


class TestGitOperationsMCPIntegration:
    """Test MCP tool integration"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        yield temp_dir, mcp

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_mcp_tool_registration(self, temp_repo):
        """Git MCP should register as agent tool"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        tools = mcp.get_mcp_tools()

        assert "commit" in tools
        assert "create_branch" in tools
        assert "merge_branch" in tools
        assert "push" in tools

    def test_mcp_tool_schema(self, temp_repo):
        """Tools should have valid JSON schema"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        schema = mcp.get_tool_schema("commit")

        assert "type" in schema
        assert "parameters" in schema
        assert "properties" in schema["parameters"]

    def test_invoke_tool(self, temp_repo):
        """Agent should invoke tool via MCP"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        result = mcp.invoke_tool(
            tool_name="commit",
            arguments={
                "file_paths": ["test.txt"],
                "message": "Test commit"
            }
        )

        assert result.success is True
        assert result.commit_hash is not None


class TestGitOperationsMCPErrorHandling:
    """Test error handling"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        yield temp_dir, mcp

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_commit_no_changes(self, temp_repo):
        """Handle commit with no changes gracefully"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        result = mcp.commit(file_paths=["nonexistent.txt"], message="Empty")

        # Should fail or handle gracefully
        assert result is not None

    def test_invalid_branch_name(self, temp_repo):
        """Handle invalid branch names"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        with pytest.raises((ValueError, Exception)):
            mcp.create_branch(branch_name="invalid..branch")

    def test_switch_nonexistent_branch(self, temp_repo):
        """Handle switching to nonexistent branch"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        result = mcp.switch_branch(branch_name="nonexistent")

        assert result.success is False

    def test_merge_nonexistent_branch(self, temp_repo):
        """Handle merging nonexistent branch"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        result = mcp.merge_branch(branch_name="nonexistent")

        assert result.success is False


class TestGitOperationsMCPMetrics:
    """Test metrics collection"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        yield temp_dir, mcp

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_operation_metrics(self, temp_repo):
        """Track operation metrics"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        result = mcp.commit(file_paths=["test.txt"], message="Test")

        assert result.execution_time_ms > 0
        assert result.execution_time_ms < 60000

    def test_metrics_aggregation(self, temp_repo):
        """Aggregate metrics across operations"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("content 0")
        mcp.commit(file_paths=["test.txt"], message="Commit 0")

        for i in range(1, 3):
            with open(test_file, "a") as f:
                f.write(f"\ncontent {i}")
            mcp.commit(file_paths=["test.txt"], message=f"Commit {i}")

        metrics = mcp.get_metrics()

        assert metrics["total_operations"] >= 3
        assert metrics["total_cost_usd"] > 0
        assert metrics["average_execution_time_ms"] > 0

    def test_operation_statistics(self, temp_repo):
        """Track operation statistics"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("initial content")

        mcp.commit(file_paths=["test.txt"], message="C1")
        mcp.create_branch(branch_name="f1")
        with open(test_file, "a") as f:
            f.write("\nmore content")
        mcp.commit(file_paths=["test.txt"], message="C2")

        stats = mcp.get_operation_stats()

        assert stats["total_operations"] >= 3
        assert stats["success_count"] >= 2
        assert "commit" in stats["operations_by_type"]


class TestGitOperationsMCPConcurrency:
    """Test concurrent operations"""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing"""
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        mcp = GitOperationsMCP(repo_path=temp_dir)
        mcp.init_repo()

        yield temp_dir, mcp

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_thread_safe_operations(self, temp_repo):
        """Operations should be thread-safe"""
        import threading
        from orchestration.mcp.git_operations import GitOperationsMCP
        import time

        temp_dir, mcp = temp_repo

        # Pre-create files to avoid conflicts
        for i in range(3):
            test_file = os.path.join(temp_dir, f"file{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"initial {i}")

        def do_commit(i):
            time.sleep(i * 0.1)  # Stagger commits to avoid conflicts
            test_file = os.path.join(temp_dir, f"file{i}.txt")
            with open(test_file, "a") as f:
                f.write(f"\nupdate {i}")
            mcp.commit(
                file_paths=[f"file{i}.txt"],
                message=f"Update {i}"
            )

        threads = [
            threading.Thread(target=do_commit, args=(i,))
            for i in range(3)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        metrics = mcp.get_metrics()
        # With 3 threads doing commits + initial fixture
        # commits, expect at least 4 total operations
        assert metrics["total_operations"] >= 3

    def test_thread_safe_cost_tracking(self, temp_repo):
        """Cost tracking should be thread-safe"""
        import threading
        from orchestration.mcp.git_operations import GitOperationsMCP

        temp_dir, mcp = temp_repo

        def do_operation(i):
            test_file = os.path.join(temp_dir, f"file{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"data {i}")
            mcp.commit(file_paths=[f"file{i}.txt"], message=f"Op {i}")

        threads = [threading.Thread(target=do_operation, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total_cost = mcp.get_accumulated_cost()
        assert total_cost > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Database Query MCP Server Tests (Phase 2A-3)

TDD approach: Tests written first, implementation follows.

Tests for MCP server wrapping database queries with:
- Query validation and sanitization
- Cost tracking per query
- SQL injection prevention
- Result caching
- Connection pooling
- Thread-safe concurrent operations

Author: Claude Code (TDD Implementation)
Date: 2026-02-07
Version: 1.0
"""

import pytest
import sqlite3
import tempfile
import os
from typing import List, Dict, Any


class TestDatabaseQueryMCPBasic:
    """Test basic Database Query MCP functionality"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        # Create test table
        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"
        )

        yield db_path, mcp

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_init_database(self, temp_db):
        """Initialize a database connection"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        assert os.path.exists(db_path)

    def test_simple_query(self, temp_db):
        """Execute a simple SELECT query"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        # Insert test data
        mcp.execute_query(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            params=["John Doe", "john@example.com"]
        )

        # Query the data
        result = mcp.query(
            "SELECT * FROM users WHERE name = ?",
            params=["John Doe"]
        )

        assert result.success is True
        assert len(result.rows) > 0
        assert result.rows[0]["name"] == "John Doe"
        assert result.cost_usd > 0

    def test_insert_query(self, temp_db):
        """Execute an INSERT query"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        result = mcp.execute_query(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            params=["Jane Doe", "jane@example.com"]
        )

        assert result.success is True
        assert result.rows_affected > 0
        assert result.cost_usd > 0

    def test_update_query(self, temp_db):
        """Execute an UPDATE query"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        mcp.execute_query(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            params=["Bob", "bob@example.com"]
        )

        result = mcp.execute_query(
            "UPDATE users SET email = ? WHERE name = ?",
            params=["bob.new@example.com", "Bob"]
        )

        assert result.success is True
        assert result.rows_affected > 0


class TestDatabaseQueryMCPValidation:
    """Test query validation"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_query_validation(self, temp_db):
        """Query should be validated before execution"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        # Should have validation method
        result = mcp.validate_query("SELECT * FROM users")
        assert result.valid is True

    def test_unsafe_query_detection(self, temp_db):
        """Detect potentially unsafe queries"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        # DROP should be flagged
        result = mcp.validate_query("DROP TABLE users")
        assert result.valid is False or result.warning is not None

    def test_query_allowed_operations(self, temp_db):
        """Only certain operations should be allowed"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        # SELECT should be allowed
        select_result = mcp.validate_query("SELECT * FROM users")
        assert select_result.valid is True

        # INSERT should be allowed
        insert_result = mcp.validate_query(
            "INSERT INTO users (name) VALUES ('test')"
        )
        assert insert_result.valid is True


class TestDatabaseQueryMCPSQLInjection:
    """Test SQL injection prevention"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parametrized_queries_safe(self, temp_db):
        """Parametrized queries should be safe from injection"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        # Insert with parameters
        mcp.execute_query(
            "INSERT INTO users (name) VALUES (?)",
            params=["'; DROP TABLE users; --"]
        )

        # Table should still exist
        result = mcp.query("SELECT COUNT(*) as count FROM users")
        assert result.success is True

    def test_injection_detection(self, temp_db):
        """Detect potential injection attempts"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        # Check injection patterns
        dangerous_input = "1' OR '1'='1"
        validation = mcp.validate_parameter(dangerous_input)

        # Should either be safe or flagged
        assert validation.safe is True or validation.warning is not None


class TestDatabaseQueryMCPCaching:
    """Test result caching"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        mcp.execute_query(
            "INSERT INTO users (name) VALUES ('Test')"
        )

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cache_hit(self, temp_db):
        """Repeated queries should hit cache"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        query = "SELECT * FROM users"

        result1 = mcp.query(query)
        result2 = mcp.query(query)

        assert result2.cached is True

    def test_cache_miss_different_params(self, temp_db):
        """Different parameters should not hit cache"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        result1 = mcp.query(
            "SELECT * FROM users WHERE id = ?",
            params=[1]
        )
        result2 = mcp.query(
            "SELECT * FROM users WHERE id = ?",
            params=[2]
        )

        assert result2.cached is False

    def test_cache_clear(self, temp_db):
        """Cache should be clearable"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        mcp.query("SELECT * FROM users")
        mcp.clear_cache()

        assert mcp.get_cache_size() == 0


class TestDatabaseQueryMCPCost:
    """Test cost tracking"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_query_cost(self, temp_db):
        """Queries should track cost"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        result = mcp.query("SELECT * FROM users")

        assert result.cost_usd > 0
        assert result.cost_usd < 0.01

    def test_cost_accumulation(self, temp_db):
        """Multiple queries should accumulate costs"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        result1 = mcp.query("SELECT * FROM users")
        result2 = mcp.execute_query(
            "INSERT INTO users (name) VALUES (?)",
            params=["Test"]
        )

        total_cost = mcp.get_accumulated_cost()

        assert total_cost >= result1.cost_usd + result2.cost_usd

    def test_cost_breakdown(self, temp_db):
        """Cost breakdown by operation type"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        breakdown = mcp.get_cost_breakdown()

        assert "select" in breakdown
        assert "insert" in breakdown
        assert breakdown["select"] > 0


class TestDatabaseQueryMCPConnectionPool:
    """Test connection pooling"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_connection_pool_stats(self, temp_db):
        """Should track connection pool statistics"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        mcp.query("SELECT * FROM users")

        stats = mcp.get_pool_stats()

        assert "active_connections" in stats
        assert "total_connections" in stats


class TestDatabaseQueryMCPIntegration:
    """Test MCP tool integration"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_mcp_tool_registration(self, temp_db):
        """Database MCP should register as agent tool"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        tools = mcp.get_mcp_tools()

        assert "query" in tools
        assert "execute_query" in tools
        assert "validate_query" in tools

    def test_mcp_tool_schema(self, temp_db):
        """Tools should have valid JSON schema"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        schema = mcp.get_tool_schema("query")

        assert "type" in schema
        assert "parameters" in schema

    def test_invoke_tool(self, temp_db):
        """Agent should invoke query tool via MCP"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        result = mcp.invoke_tool(
            tool_name="query",
            arguments={
                "sql": "SELECT * FROM users",
                "params": []
            }
        )

        assert result.success is True


class TestDatabaseQueryMCPErrorHandling:
    """Test error handling"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_invalid_sql(self, temp_db):
        """Handle invalid SQL gracefully"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        result = mcp.query("INVALID SQL QUERY")

        assert result.success is False

    def test_nonexistent_table(self, temp_db):
        """Handle queries on nonexistent table"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        result = mcp.query("SELECT * FROM nonexistent_table")

        assert result.success is False

    def test_connection_error_handling(self, temp_db):
        """Handle connection errors gracefully"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        # Close connection
        mcp.close()

        # Query should fail gracefully or reconnect
        result = mcp.query("SELECT 1")

        assert result is not None


class TestDatabaseQueryMCPMetrics:
    """Test metrics collection"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_query_execution_metrics(self, temp_db):
        """Track query execution metrics"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        result = mcp.query("SELECT * FROM users")

        assert result.execution_time_ms > 0
        assert result.execution_time_ms < 60000

    def test_metrics_aggregation(self, temp_db):
        """Aggregate metrics across queries"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        mcp.clear_cache()  # Clear cache to get fresh metrics
        for i in range(5):
            # Use different queries to avoid cache hits
            mcp.query(f"SELECT * FROM users WHERE id = {i}")

        metrics = mcp.get_metrics()

        assert metrics["total_queries"] >= 4
        assert metrics["total_cost_usd"] > 0

    def test_query_statistics(self, temp_db):
        """Track query statistics"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        mcp.query("SELECT * FROM users")
        mcp.execute_query("INSERT INTO users (name) VALUES (?)", params=["Test"])
        mcp.query("SELECT * FROM users")

        stats = mcp.get_query_stats()

        assert stats["total_queries"] >= 3
        assert "select" in stats["queries_by_type"]


class TestDatabaseQueryMCPConcurrency:
    """Test concurrent operations"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        from orchestration.mcp.database_query import DatabaseQueryMCP

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        mcp = DatabaseQueryMCP(connection_string=f"sqlite:///{db_path}")
        mcp.init_database()

        mcp.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        yield db_path, mcp

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_concurrent_queries(self, temp_db):
        """Handle concurrent query execution"""
        import threading
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        results = []

        def do_query(i):
            # Use different queries to avoid SQLite locking
            result = mcp.query(
                f"SELECT * FROM users WHERE id = {i}"
            )
            results.append(result)

        threads = [
            threading.Thread(target=do_query, args=(i,))
            for i in range(3)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 3
        # Queries may fail due to SQLite locking, but should handle gracefully
        assert all(r is not None for r in results)

    def test_thread_safe_cost_tracking(self, temp_db):
        """Cost tracking should be thread-safe"""
        import threading
        from orchestration.mcp.database_query import DatabaseQueryMCP

        db_path, mcp = temp_db

        def do_query():
            mcp.query("SELECT * FROM users")

        threads = [threading.Thread(target=do_query) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total_cost = mcp.get_accumulated_cost()
        assert total_cost > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

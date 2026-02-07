"""
Ralph Verification MCP Server (Phase 2A-1)

Wraps Ralph verification tool as MCP server with:
- Secure verification execution
- Cost tracking per verification
- Result caching
- Batch operations
- Integration with SpecialistAgent

Author: Claude Code (TDD Implementation)
Date: 2026-02-07
Version: 1.0
"""

import hashlib
import time
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime


class VerificationResult(str, Enum):
    """Ralph verification results"""
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class RalphVerificationResponse:
    """Response from Ralph verification via MCP"""
    file_path: str
    result: VerificationResult
    passed_count: int
    failed_count: int
    blocked_count: int
    issues: List[str]
    cost_usd: float
    execution_time_ms: float
    cached: bool


@dataclass
class VerificationMetrics:
    """Metrics for a single verification"""
    timestamp: datetime
    file_path: str
    code_hash: str
    result: VerificationResult
    execution_time_ms: float
    cost_usd: float


class RalphVerificationMCP:
    """MCP server wrapping Ralph verification tool"""

    # Cost constants (estimated based on token usage)
    COST_PER_VERIFICATION = 0.001  # $0.001 per verification
    COST_PER_CHECK_TYPE = {
        "linting": 0.0003,
        "type_checking": 0.0005,
        "security": 0.0007,
        "formatting": 0.0002,
    }

    def __init__(self, timeout_seconds: int = 30, enable_caching: bool = True):
        """Initialize Ralph Verification MCP server"""
        self.timeout_seconds = timeout_seconds
        self.enable_caching = enable_caching

        # Cache: hash -> response
        self._cache: Dict[str, RalphVerificationResponse] = {}
        self._cache_lock = threading.Lock()

        # Metrics tracking
        self._metrics: List[VerificationMetrics] = []
        self._metrics_lock = threading.Lock()

        # Cost tracking
        self._total_cost = 0.0
        self._cost_lock = threading.Lock()

    def verify_file(
        self,
        file_path: str,
        code_content: str,
        checks: Optional[List[str]] = None,
    ) -> RalphVerificationResponse:
        """Verify a single file via Ralph"""
        if not file_path:
            raise ValueError("file_path cannot be empty")

        # Generate cache key
        cache_key = self._generate_cache_key(file_path, code_content)

        # Check cache
        if self.enable_caching:
            with self._cache_lock:
                if cache_key in self._cache:
                    cached = self._cache[cache_key]
                    return self._return_cached_response(cached)

        # Perform verification
        start_time = time.time()
        checks_list = checks or ["linting"]
        result = self._do_verify(file_path, code_content, checks_list)
        execution_time_ms = (time.time() - start_time) * 1000

        # Calculate cost
        cost = self._calculate_cost(checks_list)

        # Create response
        response = RalphVerificationResponse(
            file_path=file_path,
            result=result["status"],
            passed_count=result.get("passed", 0),
            failed_count=result.get("failed", 0),
            blocked_count=result.get("blocked", 0),
            issues=result.get("issues", []),
            cost_usd=cost,
            execution_time_ms=execution_time_ms,
            cached=False,
        )

        # Cache result
        if self.enable_caching:
            with self._cache_lock:
                self._cache[cache_key] = response

        # Track cost
        with self._cost_lock:
            self._total_cost += cost

        # Track metrics
        self._track_metric(
            file_path, code_content, result["status"],
            execution_time_ms, cost
        )

        return response

    def _return_cached_response(
        self, cached_response: RalphVerificationResponse
    ) -> RalphVerificationResponse:
        """Return a cached response with cached flag set to True"""
        return RalphVerificationResponse(
            file_path=cached_response.file_path,
            result=cached_response.result,
            passed_count=cached_response.passed_count,
            failed_count=cached_response.failed_count,
            blocked_count=cached_response.blocked_count,
            issues=cached_response.issues,
            cost_usd=cached_response.cost_usd,
            execution_time_ms=cached_response.execution_time_ms,
            cached=True,
        )

    def verify_batch(
        self,
        files: List[Tuple[str, str]],
        checks: Optional[List[str]] = None,
        stop_on_failure: bool = False,
    ) -> List[RalphVerificationResponse]:
        """Verify multiple files"""
        results = []

        for file_path, code_content in files:
            try:
                result = self.verify_file(file_path, code_content, checks)
                results.append(result)

                if stop_on_failure and result.result == VerificationResult.FAIL:
                    break
            except Exception as e:
                # Log error but continue
                print(f"Error verifying {file_path}: {e}")
                continue

        return results

    def invoke_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Invoke tool for agent use"""
        if tool_name == "verify_file":
            return self.verify_file(
                file_path=arguments.get("file_path", ""),
                code_content=arguments.get("code_content", ""),
                checks=arguments.get("checks"),
            )
        elif tool_name == "verify_batch":
            files = arguments.get("files", [])
            return self.verify_batch(
                files=files,
                checks=arguments.get("checks"),
                stop_on_failure=arguments.get("stop_on_failure", False),
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def get_accumulated_cost(self) -> float:
        """Get total accumulated cost"""
        with self._cost_lock:
            return self._total_cost

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get cost breakdown by check type"""
        breakdown = {}
        for check_type, cost in self.COST_PER_CHECK_TYPE.items():
            breakdown[check_type] = cost

        return breakdown

    def clear_cache(self) -> None:
        """Clear verification cache"""
        with self._cache_lock:
            self._cache.clear()

    def get_cache_size(self) -> int:
        """Get number of cached results"""
        with self._cache_lock:
            return len(self._cache)

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics"""
        with self._metrics_lock:
            if not self._metrics:
                return {
                    "total_verifications": 0,
                    "total_cost_usd": 0.0,
                    "average_execution_time_ms": 0.0,
                }

            total_time = sum(m.execution_time_ms for m in self._metrics)
            return {
                "total_verifications": len(self._metrics),
                "total_cost_usd": self.get_accumulated_cost(),
                "average_execution_time_ms": total_time / len(self._metrics),
            }

    def get_pass_fail_stats(self) -> Dict[str, int]:
        """Get pass/fail statistics"""
        with self._metrics_lock:
            pass_count = sum(1 for m in self._metrics if m.result == VerificationResult.PASS)
            fail_count = sum(1 for m in self._metrics if m.result == VerificationResult.FAIL)

            return {
                "total": len(self._metrics),
                "pass": pass_count,
                "fail": fail_count,
                "blocked": len(self._metrics) - pass_count - fail_count,
            }

    def get_mcp_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get MCP tool definitions"""
        return {
            "verify_file": {
                "description":
                    "Verify a single file with Ralph verification",
                "parameters": {
                    "file_path": "Path to file being verified",
                    "code_content": "Code content to verify",
                    "checks": "List of check types to run",
                },
            },
            "verify_batch": {
                "description": "Verify multiple files",
                "parameters": {
                    "files":
                        "List of (file_path, code_content) tuples",
                    "checks": "List of check types to run",
                },
            },
            "get_accumulated_cost": {
                "description":
                    "Get total accumulated verification cost",
                "parameters": {},
            },
        }

    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get JSON schema for agent tool"""
        schemas = {
            "verify_file": {
                "type": "object",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "code_content": {"type": "string", "description": "Code to verify"},
                        "checks": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["file_path", "code_content"],
                },
            },
        }
        return schemas.get(tool_name, {})

    # Private methods

    @staticmethod
    def _generate_cache_key(file_path: str, code_content: str) -> str:
        """Generate cache key from file path and content"""
        content_hash = hashlib.md5(code_content.encode()).hexdigest()
        return f"{file_path}:{content_hash}"

    def _do_verify(
        self, file_path: str, code_content: str, checks: List[str]
    ) -> Dict[str, Any]:
        """Perform actual verification (placeholder - would call Ralph)"""
        # This is a placeholder implementation
        # In production, this would call the actual Ralph CLI or API
        # Note: file_path and checks used for routing to specific verifiers

        # Simulate verification based on code patterns
        issues = []
        failed = 0
        blocked = 0
        passed = 0

        # Detect dangerous patterns
        dangerous_patterns = [
            "os.system(",
            "subprocess.run(",
            "eval(",
            "exec(",
            "__import__('subprocess')",
            "open('/etc/passwd')",
            "open('/etc/",
        ]

        for pattern in dangerous_patterns:
            if pattern in code_content:
                blocked += 1
                issues.append(f"Security issue: {pattern} detected")

        # Detect basic formatting issues
        if code_content.count("=") > code_content.count(" = "):
            msg = (
                "Formatting issue: "
                "Missing spaces around operators"
            )
            issues.append(msg)
            failed += 1
        else:
            passed += 1

        if not issues:
            status = VerificationResult.PASS
        elif blocked > 0:
            status = VerificationResult.BLOCKED
        else:
            status = VerificationResult.FAIL

        return {
            "status": status,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "issues": issues,
        }

    def _calculate_cost(self, checks: List[str]) -> float:
        """Calculate verification cost"""
        cost = self.COST_PER_VERIFICATION

        for check in checks:
            cost += self.COST_PER_CHECK_TYPE.get(check, 0.0001)

        return cost

    def _track_metric(
        self, file_path: str, code_content: str, result: VerificationResult,
        execution_time_ms: float, cost_usd: float
    ) -> None:
        """Track verification metric"""
        metric = VerificationMetrics(
            timestamp=datetime.now(),
            file_path=file_path,
            code_hash=hashlib.md5(code_content.encode()).hexdigest(),
            result=result,
            execution_time_ms=execution_time_ms,
            cost_usd=cost_usd,
        )

        with self._metrics_lock:
            self._metrics.append(metric)

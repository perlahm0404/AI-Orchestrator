"""
AI Orchestrator MCP Server Entry Point

Run with: python -m orchestration.mcp
"""

import asyncio
from orchestration.mcp.orchestrator_server import main

if __name__ == "__main__":
    asyncio.run(main())

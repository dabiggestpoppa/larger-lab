"""
PO Tools API — FastAPI router for all PO capabilities.

Exposes all tools as REST endpoints so PO (and any client) can:
- Discover available tools
- Execute any tool with arguments
- Get tool schemas for LLM function calling

Endpoints:
  GET  /api/po/tools              — List all available tools
  GET  /api/po/tools/{category}   — List tools by category
  POST /api/po/tools/execute      — Execute a tool by name
  GET  /api/po/tools/schema       — Get OpenAI-format tool schemas
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import logging

from .po_capabilities import execute_tool, CAPABILITY_FUNCTIONS
from .po_tool_registry import ToolRegistry

logger = logging.getLogger("oce.po_tools_api")

router = APIRouter(prefix="/api/po/tools", tags=["po-tools"])

# Initialize the tool registry
_registry = ToolRegistry()


# ─── Request/Response Models ────────────────────────────────────────────────

class ToolExecuteRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str
    arguments: Dict[str, Any] = {}


class ToolExecuteResponse(BaseModel):
    """Response from tool execution."""
    tool_name: str
    result: str
    success: bool = True
    error: str = ""


class ToolInfo(BaseModel):
    """Information about a single tool."""
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]


class ToolListResponse(BaseModel):
    """List of tools."""
    tools: List[ToolInfo]
    total: int
    categories: Dict[str, int]


class ToolSchemaResponse(BaseModel):
    """OpenAI-format tool schemas."""
    tools: List[Dict[str, Any]]
    total: int


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("", response_model=ToolListResponse)
async def list_tools(category: Optional[str] = Query(None, description="Filter by category")):
    """
    List all available tools, optionally filtered by category.

    Categories: file, git, exec, search, github, browser, memory,
                vscode, notebook, pdf, system
    """
    if category:
        tool_defs = _registry.list_tools(category)
    else:
        tool_defs = _registry.list_tools()

    tools = [
        ToolInfo(
            name=t.name,
            description=t.description,
            category=t.category,
            parameters=t.parameters,
        )
        for t in tool_defs
    ]

    # Count by category
    cats: Dict[str, int] = {}
    for t in _registry.list_tools():
        cats[t.category] = cats.get(t.category, 0) + 1

    return ToolListResponse(
        tools=tools,
        total=len(tools),
        categories=cats,
    )


@router.get("/schema", response_model=ToolSchemaResponse)
async def get_tool_schemas():
    """
    Get all tool schemas in OpenAI function calling format.
    Use this to populate the tools array for LLM API calls.
    """
    schemas = _registry.to_openai_tools()
    return ToolSchemaResponse(tools=schemas, total=len(schemas))


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool_endpoint(request: ToolExecuteRequest):
    """
    Execute a tool by name with the given arguments.

    Available tools:
    - File: list_directory, read_file, write_file, edit_file, multi_edit_file, create_directory, delete_file, file_exists
    - Git: git_status, git_log, git_diff, git_commit, git_push, git_pull, git_branch, git_stash, git_blame
    - Exec: run_command, execute_python, run_python_file, install_python_package
    - Search: search_files, search_content, grep_search, web_search, web_fetch
    - GitHub: github_pr_list, github_pr_create, github_pr_view, github_pr_merge, github_issue_list, github_issue_create, github_ci_status, github_search, github_repo_info
    - System: system_env, system_processes, system_kill_process, system_disk_usage, system_info
    - Memory: memory_read, memory_write, memory_list, memory_search
    - Vault: vault_search, vault_read
    - VS Code: vscode_run_command, vscode_get_errors
    - Notebook: notebook_list, notebook_read
    - PDF: pdf_extract_text, pdf_merge, pdf_split, pdf_compress
    - Tasks: task_list, task_update
    """
    if request.tool_name not in CAPABILITY_FUNCTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tool: {request.tool_name}. Use GET /api/po/tools to list available tools."
        )

    try:
        result = execute_tool(request.tool_name, request.arguments)
        success = not result.startswith(("Error", "BLOCKED", "Unknown"))
        return ToolExecuteResponse(
            tool_name=request.tool_name,
            result=result,
            success=success,
            error="" if success else result,
        )
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories():
    """List all tool categories and their counts."""
    cats: Dict[str, int] = {}
    for t in _registry.list_tools():
        cats[t.category] = cats.get(t.category, 0) + 1
    return {"categories": cats, "total_categories": len(cats)}


@router.get("/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific tool."""
    tool = _registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
    return {
        "name": tool.name,
        "description": tool.description,
        "category": tool.category,
        "parameters": tool.parameters,
        "openai_schema": tool.to_openai(),
    }

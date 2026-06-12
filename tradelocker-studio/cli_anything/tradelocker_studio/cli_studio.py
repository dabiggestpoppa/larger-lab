"""
TradeLocker Studio CLI — Command-line interface for bot development.

Commands:
    auth            - Login and manage credentials
    project         - List/create/clone/delete bot projects
    code            - Read/write bot code
    backtest        - Run and monitor backtests
    config          - Get/set strategy configuration (symbol, resolution, dates)
    chat            - Send messages to Studio AI and read responses
    status          - Check Studio engine health
"""

import json
import sys
import os
from typing import Optional

import click

from .core.config import load_config, save_config, get_studio_host, get_account_info
from .core.auth import login as do_login, get_all_accounts
from .core.studio_client import (
    list_projects, get_project, create_project, rename_project,
    clone_project, delete_project,
    get_file_content, update_file_content,
    start_process, get_process, stop_process,
    get_strategy_config, update_strategy_config,
    get_conversation_messages, send_conversation_message,
    poll_process_until_complete, health_check, get_limits,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_output(data, pretty: bool = True):
    """Output data as JSON."""
    if pretty:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(json.dumps(data, default=str))


def _get_project_id(ctx) -> str:
    """Get project ID from context or prompt."""
    project_id = ctx.obj.get("project_id") if ctx.obj else None
    if not project_id:
        project_id = click.prompt("Project ID")
    return project_id


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.option("--json-output", is_flag=True, default=False, help="Compact JSON output")
@click.option("--project-id", "-p", default=None, help="Default project ID for commands")
@click.pass_context
def cli(ctx, json_output, project_id):
    """TradeLocker Studio CLI — Write bot code, run backtests, read results.

    \b
    Quick start:
        tl-studio auth login
        tl-studio project list
        tl-studio code write --project-id <id> --file-id <id> --code "your bot code"
        tl-studio backtest run --project-id <id>
        tl-studio backtest results --project-id <id> --process-id <id>
    """
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output
    ctx.obj["project_id"] = project_id

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ---------------------------------------------------------------------------
# Auth commands
# ---------------------------------------------------------------------------

@cli.group()
def auth():
    """Manage TradeLocker authentication."""
    pass


@auth.command("login")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--server", prompt=True)
@click.option("--environment", default="demo", type=click.Choice(["demo", "live"]))
def auth_login(email, password, server, environment):
    """Login to TradeLocker and save credentials."""
    result = do_login(email, password, server, environment)
    save_config({
        "email": email,
        "password": password,
        "server": server,
        "environment": environment,
        "jwt_token": result.get("accessToken", ""),
        "refresh_token": result.get("refreshToken", ""),
    })
    click.echo("✓ Credentials saved to ~/.tradelocker-studio/config.json")
    click.echo(f"  Environment: {environment}")
    click.echo(f"  Token expires: {result.get('expireDate', 'unknown')}")


@auth.command("status")
def auth_status():
    """Check current authentication status."""
    config = load_config()
    click.echo(f"Email: {config.get('email', 'not set')}")
    click.echo(f"Server: {config.get('server', 'not set')}")
    click.echo(f"Environment: {config.get('environment', 'not set')}")
    click.echo(f"JWT Token: {'set' if config.get('jwt_token') else 'not set'}")
    click.echo(f"Refresh Token: {'set' if config.get('refresh_token') else 'not set'}")


@auth.command("accounts")
def auth_accounts():
    """List all TradeLocker accounts."""
    config = load_config()
    jwt_token = config.get("jwt_token", "")
    if not jwt_token:
        click.echo("Not logged in. Run 'tl-studio auth login' first.", err=True)
        sys.exit(1)
    result = get_all_accounts(jwt_token, config.get("environment", "demo"))
    _json_output(result)


# ---------------------------------------------------------------------------
# Project commands
# ---------------------------------------------------------------------------

@cli.group()
def project():
    """Manage bot projects."""
    pass


@project.command("list")
def project_list():
    """List all bot projects."""
    result = list_projects()
    _json_output(result)


@project.command("create")
@click.option("--name", default="New Bot", help="Project name")
def project_create(name):
    """Create a new bot project."""
    result = create_project(name)
    _json_output(result)


@project.command("get")
@click.argument("project_id", required=False)
def project_get(project_id):
    """Get project details."""
    if not project_id:
        project_id = click.prompt("Project ID")
    result = get_project(project_id)
    _json_output(result)


@project.command("rename")
@click.argument("project_id", required=False)
@click.option("--name", prompt=True, help="New name")
def project_rename(project_id, name):
    """Rename a project."""
    if not project_id:
        project_id = click.prompt("Project ID")
    result = rename_project(project_id, name)
    _json_output(result)


@project.command("clone")
@click.argument("project_id", required=False)
def project_clone(project_id):
    """Clone an existing project."""
    if not project_id:
        project_id = click.prompt("Project ID")
    result = clone_project(project_id)
    _json_output(result)


@project.command("delete")
@click.argument("project_id", required=False)
@click.option("--stop", is_flag=True, default=False, help="Stop running processes first")
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
def project_delete(project_id, stop):
    """Delete a project."""
    if not project_id:
        project_id = click.prompt("Project ID")
    result = delete_project(project_id, should_stop=stop)
    _json_output(result)


# ---------------------------------------------------------------------------
# Code commands
# ---------------------------------------------------------------------------

@cli.group()
def code():
    """Read and write bot code."""
    pass


@code.command("read")
@click.argument("file_id")
def code_read(file_id):
    """Read bot code from a strategy file."""
    content = get_file_content(file_id)
    click.echo(content)


@code.command("write")
@click.argument("file_id")
@click.option("--code", "-c", default=None, help="Code to write (or reads from stdin)")
@click.option("--file", "-f", "code_file", default=None, help="Read code from file")
def code_write(file_id, code, code_file):
    """Write bot code to a strategy file.

    \b
    Examples:
        tl-studio code write <file-id> --code "strategy('My Bot')"
        echo "strategy('My Bot')" | tl-studio code write <file-id>
        tl-studio code write <file-id> --file my_bot.tl
    """
    if code_file:
        with open(code_file) as f:
            code = f.read()
    elif code is None:
        if sys.stdin.isatty():
            code = click.edit("Enter your bot code here...")
            if code is None:
                click.echo("No code provided.", err=True)
                sys.exit(1)
        else:
            code = sys.stdin.read()

    result = update_file_content(file_id, code)
    click.echo(f"✓ Code written to file {file_id}")
    click.echo(f"  Length: {len(code)} characters")


@code.command("edit")
@click.argument("file_id")
def code_edit(file_id):
    """Open bot code in external editor ($EDITOR)."""
    content = get_file_content(file_id)
    edited = click.edit(content)
    if edited and edited != content:
        result = update_file_content(file_id, edited)
        click.echo(f"✓ Code updated in file {file_id}")
    else:
        click.echo("No changes.")


# ---------------------------------------------------------------------------
# Backtest commands
# ---------------------------------------------------------------------------

@cli.group()
def backtest():
    """Run and monitor backtests."""
    pass


@backtest.command("run")
@click.argument("project_id", required=False)
@click.option("--symbol", "-s", default=None, help="Symbol to backtest (e.g., AUDCAD)")
@click.option("--resolution", "-r", default="1m", help="Resolution (1m, 5m, 1h, 1D)")
@click.option("--start-date", default=None, help="Start date (ISO format)")
@click.option("--end-date", default=None, help="End date (ISO format)")
@click.option("--margin", default=None, type=float, help="Margin amount")
@click.option("--leverage", default=None, type=float, help="Leverage multiplier")
@click.option("--wait", is_flag=True, default=False, help="Wait for backtest to complete")
@click.option("--poll-interval", default=2.0, type=float, help="Polling interval in seconds")
def backtest_run(project_id, symbol, resolution, start_date, end_date, margin, leverage, wait, poll_interval):
    """Start a backtest for a bot project.

    \b
    Examples:
        tl-studio backtest run --project-id <id>
        tl-studio backtest run --project-id <id> --symbol AUDCAD --resolution 1h
        tl-studio backtest run --project-id <id> --wait --poll-interval 5
    """
    if not project_id:
        project_id = click.prompt("Project ID")

    # Build strategy config
    config = {}
    if symbol:
        config["symbolName"] = symbol
    if resolution:
        config["resolution"] = resolution
    if start_date:
        config["startDate"] = start_date
    if end_date:
        config["endDate"] = end_date
    if margin is not None:
        config["margin"] = margin
    if leverage is not None:
        config["leverage"] = leverage

    # Get account info for authentication
    acct = get_account_info()
    if not acct.get("refresh_token"):
        click.echo("No refresh token. Run 'tl-studio auth login' first.", err=True)
        sys.exit(1)

    result = start_process(
        project_id=project_id,
        refresh_token=acct["refresh_token"],
        account_id=int(acct.get("account_id", 0)),
        acc_num=int(acct.get("acc_num", 1)),
        strategy_config=config if config else None,
    )

    process_id = result.get("id", result.get("processId", ""))
    click.echo(f"✓ Backtest started: {process_id}")
    _json_output(result)

    if wait:
        click.echo("Waiting for backtest to complete...")

        def on_poll(proc):
            status = proc.get("status", "unknown")
            click.echo(f"  Status: {status}", nl=False)
            if proc.get("result"):
                res = proc["result"]
                click.echo(f" | Trades: {res.get('total_trades', '?')} | ROI: {res.get('roi_percent', '?')}%", nl=False)
            click.echo()

        final = poll_process_until_complete(
            project_id, process_id,
            poll_interval=poll_interval,
            callback=on_poll,
        )
        click.echo("\n✓ Backtest complete:")
        _json_output(final)


@backtest.command("results")
@click.argument("project_id", required=False)
@click.argument("process_id", required=False)
def backtest_results(project_id, process_id):
    """Get backtest results."""
    if not project_id:
        project_id = click.prompt("Project ID")
    if not process_id:
        process_id = click.prompt("Process ID")
    result = get_process(project_id, process_id)
    _json_output(result)


@backtest.command("stop")
@click.argument("project_id", required=False)
@click.argument("process_id", required=False)
def backtest_stop(project_id, process_id):
    """Stop a running backtest."""
    if not project_id:
        project_id = click.prompt("Project ID")
    if not process_id:
        process_id = click.prompt("Process ID")
    result = stop_process(project_id, process_id)
    click.echo(f"✓ Backtest stopped: {process_id}")
    _json_output(result)


@backtest.command("issue")
@click.argument("project_id", required=False)
@click.argument("process_id", required=False)
def backtest_issue(project_id, process_id):
    """Get process issue/diagnostic info."""
    if not project_id:
        project_id = click.prompt("Project ID")
    if not process_id:
        process_id = click.prompt("Process ID")
    result = get_process_issue(project_id, process_id)
    _json_output(result)


# ---------------------------------------------------------------------------
# Config commands
# ---------------------------------------------------------------------------

@cli.group()
def config():
    """Get/set strategy configuration (symbol, resolution, dates, margin)."""
    pass


@config.command("get")
@click.argument("project_id", required=False)
def config_get(project_id):
    """Get current strategy configuration."""
    if not project_id:
        project_id = click.prompt("Project ID")
    result = get_strategy_config(project_id)
    _json_output(result)


@config.command("set")
@click.argument("project_id", required=False)
@click.option("--symbol", "-s", default=None, help="Symbol (e.g., AUDCAD)")
@click.option("--resolution", "-r", default=None, help="Resolution (1m, 5m, 1h, 1D)")
@click.option("--start-date", default=None, help="Start date (ISO format)")
@click.option("--end-date", default=None, help="End date (ISO format)")
@click.option("--margin", default=None, type=float, help="Margin amount")
@click.option("--leverage", default=None, type=float, help="Leverage multiplier")
@click.option("--commission", default=None, type=float, help="Commission")
def config_set(project_id, symbol, resolution, start_date, end_date, margin, leverage, commission):
    """Update strategy configuration."""
    if not project_id:
        project_id = click.prompt("Project ID")

    current = get_strategy_config(project_id)

    if symbol:
        current["symbolName"] = symbol
    if resolution:
        current["resolution"] = resolution
    if start_date:
        current["startDate"] = start_date
    if end_date:
        current["endDate"] = end_date
    if margin is not None:
        current["margin"] = margin
    if leverage is not None:
        current["leverage"] = leverage
    if commission is not None:
        current["commission"] = commission

    result = update_strategy_config(project_id, current)
    click.echo("✓ Strategy configuration updated:")
    _json_output(result)


# ---------------------------------------------------------------------------
# Chat commands (AI)
# ---------------------------------------------------------------------------

@cli.group()
def chat():
    """Interact with Studio AI chatbot."""
    pass


@chat.command("send")
@click.argument("conversation_id")
@click.option("--message", "-m", prompt=True, help="Message to send")
def chat_send(conversation_id, message):
    """Send a message to the AI chatbot."""
    result = send_conversation_message(conversation_id, message)
    _json_output(result)


@chat.command("history")
@click.argument("conversation_id")
def chat_history(conversation_id):
    """Get conversation history."""
    messages = get_conversation_messages(conversation_id)
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        click.echo(f"[{role}] {content}")
        click.echo()


# ---------------------------------------------------------------------------
# Status command
# ---------------------------------------------------------------------------

@cli.command("status")
def studio_status():
    """Check Studio engine health and limits."""
    try:
        health = health_check()
        click.echo("✓ Studio engine: healthy")
        _json_output(health)
    except Exception as e:
        click.echo(f"✗ Studio engine: {e}", err=True)
        click.echo("  Make sure TradeLocker Desktop is running with --remote-debugging-port=9222")

    try:
        limits = get_limits()
        click.echo("\nRate limits:")
        _json_output(limits)
    except Exception as e:
        click.echo(f"Could not fetch limits: {e}", err=True)


if __name__ == "__main__":
    cli()

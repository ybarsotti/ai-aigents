#!/usr/bin/env python3
import json
import os
import subprocess
import requests
from typing import Optional
from pathlib import Path

from mcp.types import TextContent
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("pr-agent")

# PR template directory (shared between starter and solution)
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
EVENTS_FILE = Path(__file__).parent / "github_events.json"

# Default PR templates
DEFAULT_TEMPLATES = {
    "bug.md": "Bug Fix",
    "feature.md": "Feature",
    "docs.md": "Documentation",
    "refactor.md": "Refactor",
    "test.md": "Test",
    "performance.md": "Performance",
    "security.md": "Security",
}

# Type mapping for PR templates
TYPE_MAPPING = {
    "bug": "bug.md",
    "fix": "bug.md",
    "feature": "feature.md",
    "enhancement": "feature.md",
    "docs": "docs.md",
    "documentation": "docs.md",
    "refactor": "refactor.md",
    "cleanup": "refactor.md",
    "test": "test.md",
    "testing": "test.md",
    "performance": "performance.md",
    "optimization": "performance.md",
    "security": "security.md",
}


@mcp.tool()
async def analyze_file_changes(
    base_branch: str = "main",
    include_diff: bool = True,
    max_diff_lines: int = 500,
    working_directory: Optional[str] = None,
) -> str:
    """Get the full diff and list of changed files in the current git repository.

    Args:
        base_branch: Base branch to compare against (default: main)
        include_diff: Include the full diff content (default: true)
        max_diff_lines: Maximum number of diff lines to include (default: 500)
        working_directory: Directory to run git commands in (default: current directory)
    """
    try:
        # Try to get working directory from roots first
        if working_directory is None:
            try:
                context = mcp.get_context()
                roots_result = await context.session.list_roots()
                # Get the first root - Claude Code sets this to the CWD
                root = roots_result.roots[0]
                # FileUrl object has a .path property that gives us the path directly
                working_directory = root.uri.path
            except Exception:
                # If we can't get roots, fall back to current directory
                pass

        # Use provided working directory or current directory
        cwd = working_directory if working_directory else os.getcwd()

        # Debug output
        debug_info = {
            "provided_working_directory": working_directory,
            "actual_cwd": cwd,
            "server_process_cwd": os.getcwd(),
            "server_file_location": str(Path(__file__).parent),
            "roots_check": None,
        }

        # Add roots debug info
        try:
            context = mcp.get_context()
            roots_result = await context.session.list_roots()
            debug_info["roots_check"] = {
                "found": True,
                "count": len(roots_result.roots),
                "roots": [str(root.uri) for root in roots_result.roots],
            }
        except Exception as e:
            debug_info["roots_check"] = {"found": False, "error": str(e)}

        # Get list of changed files
        files_result = subprocess.run(
            ["git", "diff", "--name-status", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )

        # Get diff statistics
        stat_result = subprocess.run(
            ["git", "diff", "--stat", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        # Get the actual diff if requested
        diff_content = ""
        truncated = False
        if include_diff:
            diff_result = subprocess.run(
                ["git", "diff", f"{base_branch}...HEAD"],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            diff_lines = diff_result.stdout.split("\n")

            # Check if we need to truncate
            if len(diff_lines) > max_diff_lines:
                diff_content = "\n".join(diff_lines[:max_diff_lines])
                diff_content += f"\n\n... Output truncated. Showing {
                    max_diff_lines
                } of {len(diff_lines)} lines ..."
                diff_content += "\n... Use max_diff_lines parameter to see more ..."
                truncated = True
            else:
                diff_content = diff_result.stdout

        # Get commit messages for context
        commits_result = subprocess.run(
            ["git", "log", "--oneline", f"{base_branch}..HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        analysis = {
            "base_branch": base_branch,
            "files_changed": files_result.stdout,
            "statistics": stat_result.stdout,
            "commits": commits_result.stdout,
            "diff": diff_content
            if include_diff
            else "Diff not included (set include_diff=true to see full diff)",
            "truncated": truncated,
            "total_diff_lines": len(diff_lines) if include_diff else 0,
            "_debug": debug_info,
        }

        return json.dumps(analysis, indent=2)

    except subprocess.CalledProcessError as e:
        return json.dumps({"error": f"Git error: {e.stderr}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_pr_templates() -> str:
    """List available PR templates with their content."""
    templates = [
        {
            "filename": filename,
            "type": template_type,
            "content": (TEMPLATES_DIR / filename).read_text(),
        }
        for filename, template_type in DEFAULT_TEMPLATES.items()
    ]

    return json.dumps(templates, indent=2)


@mcp.tool()
async def suggest_template(changes_summary: str, change_type: str) -> str:
    """Let Claude analyze the changes and suggest the most appropriate PR template.

    Args:
        changes_summary: Your analysis of what the changes do
        change_type: The type of change you've identified (bug, feature, docs, refactor, test, etc.)
    """

    # Get available templates
    templates_response = await get_pr_templates()
    templates = json.loads(templates_response)

    # Find matching template
    template_file = TYPE_MAPPING.get(change_type.lower(), "feature.md")
    selected_template = next(
        (t for t in templates if t["filename"] == template_file),
        templates[0],  # Default to first template if no match
    )

    suggestion = {
        "recommended_template": selected_template,
        "reasoning": f"Based on your analysis: '{changes_summary}', this appears to be a {change_type} change.",
        "template_content": selected_template["content"],
        "usage_hint": "Claude can help you fill out this template based on the specific changes in your PR.",
    }

    return json.dumps(suggestion, indent=2)


@mcp.tool()
async def get_recent_actions_events(limit: int = 10) -> str:
    """Get the most recent GitHub Actions events.

    Args:
        limit: Maximum number of events to return (default: 10)
    """
    try:
        if not EVENTS_FILE.exists():
            return json.dumps([], indent=2)

        with open(EVENTS_FILE, "r") as f:
            events = json.load(f)

        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        recent_events = events[:limit]
        return json.dumps(recent_events, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to read events: {str(e)}"})


@mcp.tool()
async def get_workflow_status(workflow_name: Optional[str] = None) -> str:
    """Get the status of GitHub Actions workflows from recent events.

    Args:
       workflow_name: workflow name to filter
    """
    try:
        if not EVENTS_FILE.exists():
            return json.dumps({"error": "No events file found"})

        with open(EVENTS_FILE, "r") as f:
            events = json.load(f)

        workflow_events = [e for e in events if e.get("workflow_run") is not None]

        if workflow_name:
            workflow_events = [
                e
                for e in workflow_events
                if e["workflow_run"].get("name") == workflow_name
            ]

        workflow_status = {}
        for event in workflow_events:
            workflow_run = event.get("workflow_run", {})
            workflow_name = workflow_run.get("name")

            if workflow_name:
                if (
                    workflow_name not in workflow_status
                    or event.get("timestamp", "")
                    > workflow_status[workflow_name]["timestamp"]
                ):
                    workflow_status[workflow_name] = {
                        "status": workflow_run.get("status", "unknown"),
                        "conclusion": workflow_run.get("conclusion", "unknown"),
                        "timestamp": event.get("timestamp", ""),
                        "repository": event.get("repository", "unknown"),
                        "html_url": workflow_run.get("html_url", ""),
                    }

        return json.dumps(workflow_status, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to process workflow status: {str(e)}"})


@mcp.prompt()
async def analyze_ci_results():
    """Analyze recent CI/CD results and provide insights."""
    return """Please analyze the recent CI/CD results from GitHub Actions:

1. First, call get_recent_actions_events() to fetch the latest CI/CD events
2. Then call get_workflow_status() to check current workflow states
3. Identify any failures or issues that need attention
4. Provide actionable next steps based on the results

Format your response as:
## CI/CD Status Summary
- **Overall Health**: [Good/Warning/Critical]
- **Failed Workflows**: [List any failures with links]
- **Successful Workflows**: [List recent successes]
- **Recommendations**: [Specific actions to take]
- **Trends**: [Any patterns you notice]"""


@mcp.prompt()
async def create_deployment_summary():
    """Generate a deployment summary for team communication."""
    return """Create a deployment summary for team communication:

1. Check workflow status with get_workflow_status()
2. Look specifically for deployment-related workflows
3. Note the deployment outcome, timing, and any issues

Format as a concise message suitable for Slack:

🚀 **Deployment Update**
- **Status**: [✅ Success / ❌ Failed / ⏳ In Progress]
- **Environment**: [Production/Staging/Dev]
- **Version/Commit**: [If available from workflow data]
- **Duration**: [If available]
- **Key Changes**: [Brief summary if available]
- **Issues**: [Any problems encountered]
- **Next Steps**: [Required actions if failed]

Keep it brief but informative for team awareness."""


@mcp.prompt()
async def generate_pr_status_report():
    """Generate a comprehensive PR status report including CI/CD results."""
    return """Generate a comprehensive PR status report:

1. Use analyze_file_changes() to understand what changed
2. Use get_workflow_status() to check CI/CD status
3. Use suggest_template() to recommend the appropriate PR template
4. Combine all information into a cohesive report

Create a detailed report with:

## 📋 PR Status Report

### 📝 Code Changes
- **Files Modified**: [Count by type - .py, .js, etc.]
- **Change Type**: [Feature/Bug/Refactor/etc.]
- **Impact Assessment**: [High/Medium/Low with reasoning]
- **Key Changes**: [Bullet points of main modifications]

### 🔄 CI/CD Status
- **All Checks**: [✅ Passing / ❌ Failing / ⏳ Running]
- **Test Results**: [Pass rate, failed tests if any]
- **Build Status**: [Success/Failed with details]
- **Code Quality**: [Linting, coverage if available]

### 📌 Recommendations
- **PR Template**: [Suggested template and why]
- **Next Steps**: [What needs to happen before merge]
- **Reviewers**: [Suggested reviewers based on files changed]

### ⚠️ Risks & Considerations
- [Any deployment risks]
- [Breaking changes]
- [Dependencies affected]"""


@mcp.prompt()
async def troubleshoot_workflow_failure():
    """Help troubleshoot a failing GitHub Actions workflow."""
    return """Help troubleshoot failing GitHub Actions workflows:

1. Use get_recent_actions_events() to find recent failures
2. Use get_workflow_status() to see which workflows are failing
3. Analyze the failure patterns and timing
4. Provide systematic troubleshooting steps

Structure your response as:

## 🔧 Workflow Troubleshooting Guide

### ❌ Failed Workflow Details
- **Workflow Name**: [Name of failing workflow]
- **Failure Type**: [Test/Build/Deploy/Lint]
- **First Failed**: [When did it start failing]
- **Failure Rate**: [Intermittent or consistent]

### 🔍 Diagnostic Information
- **Error Patterns**: [Common error messages or symptoms]
- **Recent Changes**: [What changed before failures started]
- **Dependencies**: [External services or resources involved]

### 💡 Possible Causes (ordered by likelihood)
1. **[Most Likely]**: [Description and why]
2. **[Likely]**: [Description and why]
3. **[Possible]**: [Description and why]

### ✅ Suggested Fixes
**Immediate Actions:**
- [ ] [Quick fix to try first]
- [ ] [Second quick fix]

**Investigation Steps:**
- [ ] [How to gather more info]
- [ ] [Logs or data to check]

**Long-term Solutions:**
- [ ] [Preventive measure]
- [ ] [Process improvement]

### 📚 Resources
- [Relevant documentation links]
- [Similar issues or solutions]"""


@mcp.tool()
def send_slack_notification(message: str) -> str:
    """Send a formatted notification to the team Slack channel."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return "Error: SLACK_WEBHOOK_URL environment variable not set"

    try:
        payload = {"text": message, "mrkdwn": True}

        response = requests.post(
            webhook_url, json=payload, headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            return "Success: Notification sent to Slack"
        else:
            return f"Error: Failed to send notification. Status code: {response.status_code}"
    except Exception as e:
        return f"Error sending message: {str(e)}"


@mcp.prompt()
def format_ci_failure_alert() -> str:
    """Create a Slack alert for CI/CD failures."""
    return """Format this GitHub Actions failure as a Slack message:

Use this template:
:rotating_light: *CI Failure Alert* :rotating_light:

A CI workflow has failed:
*Workflow*: workflow_name
*Branch*: branch_name
*Status*: Failed
*View Details*: <LOGS_LINK|View Logs>

Please check the logs and address any issues.

Use Slack markdown formatting and keep it concise for quick team scanning."""


@mcp.prompt()
def format_ci_success_summary() -> str:
    """Create a Slack message celebrating successful deployments."""
    return """Format this successful GitHub Actions run as a Slack message:

Use this template:
:white_check_mark: *Deployment Successful* :white_check_mark:

Deployment completed successfully for [Repository Name]

*Changes:*
- Key feature or fix 1
- Key feature or fix 2

*Links:*
<PR_LINK|View Changes>

Keep it celebratory but informative. Use Slack markdown formatting."""


if __name__ == "__main__":
    mcp.run()

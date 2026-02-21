#!/usr/bin/env python3
"""
VFX Pre-Render Guard Agent

An agentic implementation that uses Claude to validate and fix USD scene files.
The agent reads a rulebook, inspects scene files using tools, reasons about
problems, applies fixes, and verifies the result — all autonomously.

Usage:
    python3 agent.py <scene_file.usda>
    python3 agent.py vfx_project_alpha/shots/shot_010/scene_v01.usda
"""

import anthropic
import json
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# Tool definitions — these are what the agent can call
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "read_file",
        "description": (
            "Read the contents of a file on disk. Use this to inspect USD scene "
            "files, textures listings, configs, or any other project file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to read.",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_directory",
        "description": (
            "List files and subdirectories in a directory. Useful for discovering "
            "available textures, assets, or shot folders."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list.",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "check_file_exists",
        "description": (
            "Check whether a specific file exists on disk. Returns true/false. "
            "Use this to verify that asset references in a scene actually resolve."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to check (absolute or relative).",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "apply_fix",
        "description": (
            "Apply a text replacement fix to a file. Replaces the first occurrence "
            "of old_text with new_text. Returns success/failure and the affected line."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to modify.",
                },
                "old_text": {
                    "type": "string",
                    "description": "The exact text to find and replace.",
                },
                "new_text": {
                    "type": "string",
                    "description": "The replacement text.",
                },
                "reason": {
                    "type": "string",
                    "description": "Why this fix is being applied (for the audit log).",
                },
            },
            "required": ["path", "old_text", "new_text", "reason"],
        },
    },
    {
        "name": "run_validation_script",
        "description": (
            "Run the deterministic pre_render_check.sh validation script against "
            "the shots directory. Returns stdout/stderr and exit code. Use this as "
            "a final backstop after applying fixes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "shots_dir": {
                    "type": "string",
                    "description": "Path to the shots directory to validate. Defaults to vfx_project_alpha/shots.",
                }
            },
            "required": [],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool execution — maps tool names to actual implementations
# ---------------------------------------------------------------------------

audit_log = []


def execute_tool(name: str, tool_input: dict) -> str:
    """Execute a tool and return the result as a string."""

    if name == "read_file":
        path = tool_input["path"]
        try:
            with open(path) as f:
                content = f.read()
            return f"Contents of {path}:\n\n{content}"
        except FileNotFoundError:
            return f"ERROR: File not found: {path}"
        except Exception as e:
            return f"ERROR: {e}"

    elif name == "list_directory":
        path = tool_input["path"]
        try:
            entries = sorted(os.listdir(path))
            listing = "\n".join(entries) if entries else "(empty directory)"
            return f"Contents of {path}/:\n{listing}"
        except FileNotFoundError:
            return f"ERROR: Directory not found: {path}"
        except Exception as e:
            return f"ERROR: {e}"

    elif name == "check_file_exists":
        path = tool_input["path"]
        exists = os.path.isfile(path)
        return json.dumps({"path": path, "exists": exists})

    elif name == "apply_fix":
        path = tool_input["path"]
        old_text = tool_input["old_text"]
        new_text = tool_input["new_text"]
        reason = tool_input["reason"]

        try:
            with open(path) as f:
                content = f.read()

            if old_text not in content:
                return f"ERROR: Could not find the text to replace in {path}:\n{old_text}"

            new_content = content.replace(old_text, new_text, 1)

            with open(path, "w") as f:
                f.write(new_content)

            # Record in audit log
            entry = {
                "file": path,
                "old": old_text.strip(),
                "new": new_text.strip(),
                "reason": reason,
            }
            audit_log.append(entry)

            return json.dumps({"status": "ok", "fix_applied": entry})

        except Exception as e:
            return f"ERROR: {e}"

    elif name == "run_validation_script":
        shots_dir = tool_input.get("shots_dir", "vfx_project_alpha/shots")
        script = os.path.join(os.path.dirname(__file__) or ".", "pre_render_check.sh")
        try:
            result = subprocess.run(
                ["bash", script, shots_dir],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout + result.stderr
            return (
                f"Exit code: {result.returncode}\n\n{output.strip()}"
            )
        except FileNotFoundError:
            return "ERROR: pre_render_check.sh not found"
        except subprocess.TimeoutExpired:
            return "ERROR: Validation script timed out after 30s"

    else:
        return f"ERROR: Unknown tool: {name}"


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------


def load_rulebook(path: str = "rulebook.md") -> str:
    """Load the natural-language rulebook."""
    rulebook_path = os.path.join(os.path.dirname(__file__) or ".", path)
    try:
        with open(rulebook_path) as f:
            return f.read()
    except FileNotFoundError:
        return "(No rulebook found — using built-in defaults)"


def run_agent(scene_path: str) -> str:
    """
    Run the agentic validation loop against a scene file.

    Returns the agent's final summary text.
    """
    rulebook = load_rulebook()

    client = anthropic.Anthropic()

    system_prompt = (
        "You are the VFX Pre-Render Guard, an AI agent that validates USD scene "
        "files before they reach the render farm. You catch errors that would waste "
        "expensive GPU hours.\n\n"
        "You have tools to read files, list directories, check file existence, "
        "apply fixes, and run a deterministic validation script.\n\n"
        "Your workflow:\n"
        "1. Read the scene file.\n"
        "2. Analyze it against the rulebook.\n"
        "3. For each issue found, use your tools to investigate (check if referenced "
        "   files exist, list available alternatives, etc.).\n"
        "4. Apply fixes using the apply_fix tool with a clear reason for each.\n"
        "5. After all fixes, run the validation script as a final check.\n"
        "6. Provide a clear summary of what you found and fixed.\n\n"
        "Be thorough but precise. Only fix real problems — don't change things that "
        "are correct. Explain each issue in plain language a VFX supervisor would "
        "understand.\n\n"
        "--- RULEBOOK ---\n"
        f"{rulebook}"
    )

    messages = [
        {
            "role": "user",
            "content": (
                f"A scene file was just saved and needs pre-render validation:\n\n"
                f"  {scene_path}\n\n"
                f"Please read it, identify any issues, fix them, and verify the result."
            ),
        }
    ]

    print(f"\n{'='*60}")
    print(f"  VFX Pre-Render Guard Agent")
    print(f"  Scene: {scene_path}")
    print(f"{'='*60}\n")

    turn = 0
    max_turns = 20  # safety limit

    while turn < max_turns:
        turn += 1

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # Collect assistant content blocks
        assistant_content = response.content

        # Print any text the agent emits
        for block in assistant_content:
            if hasattr(block, "text"):
                print(block.text)

        # If the agent is done (no more tool calls), we're finished
        if response.stop_reason == "end_turn":
            final_text = "\n".join(
                block.text for block in assistant_content if hasattr(block, "text")
            )
            return final_text

        # Process tool calls
        tool_results = []
        for block in assistant_content:
            if block.type == "tool_use":
                print(f"  [tool] {block.name}({json.dumps(block.input, indent=None)})")
                result = execute_tool(block.name, block.input)
                print(f"  [result] {result[:200]}{'...' if len(result) > 200 else ''}\n")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        # Feed results back into the conversation
        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

    return "ERROR: Agent hit maximum turn limit without completing."


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 agent.py <scene_file.usda>")
        print("Example: python3 agent.py vfx_project_alpha/shots/shot_010/scene_v01.usda")
        sys.exit(1)

    scene_path = sys.argv[1]

    if not os.path.isfile(scene_path):
        print(f"Error: Scene file not found: {scene_path}")
        sys.exit(1)

    summary = run_agent(scene_path)

    # Print audit log
    if audit_log:
        print(f"\n{'='*60}")
        print(f"  Audit Log — {len(audit_log)} fix(es) applied")
        print(f"{'='*60}")
        for i, entry in enumerate(audit_log, 1):
            print(f"\n  Fix {i}: {entry['reason']}")
            print(f"    File:  {entry['file']}")
            print(f"    Was:   {entry['old']}")
            print(f"    Now:   {entry['new']}")
    else:
        print("\n  No fixes were needed — scene is clean.")

    print()


if __name__ == "__main__":
    main()

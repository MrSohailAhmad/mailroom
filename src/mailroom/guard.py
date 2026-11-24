"""A guard for a Claude Code PreToolUse hook: it reads the tool call as JSON."""

import json
import re
from typing import cast

from mailroom.sending import SendRefused, check_recipient

SEND_TOOLS = {"send-email", "send-batch-emails"}


def short_name(tool_name: str) -> str:
    # "mcp__resend__send-email" -> "send-email"
    return tool_name.rsplit("__", 1)[-1]


def addresses(value: object) -> list[str]:
    if value is None:
        return []
    found: list[str] = []
    if isinstance(value, list):
        for item in cast(list[object], value):
            found += addresses(item)
        return found
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        # "Ayesha <ayesha@example.com>" -> "ayesha@example.com"
        bracketed = re.search(r"<([^>]+)>", part)
        found.append(bracketed.group(1).strip() if bracketed else part)
    return found


def messages(tool: str, tool_input: dict[str, object]) -> list[dict[str, object]]:
    if tool == "send-batch-emails":
        emails = tool_input.get("emails")
        if isinstance(emails, list):
            return [cast(dict[str, object], e) for e in cast(list[object], emails) if isinstance(e, dict)]
    return [tool_input]


def guard_tool_call(payload: str) -> tuple[bool, str]:
    """Return (allowed, reason). Uses the same recipient rule as sending."""
    try:
        call = cast(dict[str, object], json.loads(payload or "{}"))
    except json.JSONDecodeError:
        return False, "Mailroom guard could not read the tool call, so it was blocked."
    tool = short_name(str(call.get("tool_name", "")))
    if tool not in SEND_TOOLS:
        return True, ""
    tool_input = call.get("tool_input")
    if not isinstance(tool_input, dict):
        return False, "Mailroom guard found no tool_input, so it was blocked."
    for message in messages(tool, cast(dict[str, object], tool_input)):
        for field in ("to", "cc", "bcc"):
            for address in addresses(message.get(field)):
                try:
                    check_recipient(address)
                except SendRefused as error:
                    return False, f"Mailroom guard: {error}"
    return True, ""

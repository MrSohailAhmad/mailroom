import json
import subprocess

from mailroom.guard import guard_tool_call


def call(tool: str, tool_input: dict[str, object]) -> str:
    return json.dumps({"tool_name": tool, "tool_input": tool_input})


def test_gmail_is_blocked_with_a_reason() -> None:
    allowed, reason = guard_tool_call(call("mcp__resend__send-email", {"to": "sara.ali@gmail.com"}))
    assert not allowed
    assert "sara.ali@gmail.com" in reason


def test_practice_address_is_allowed() -> None:
    allowed, _ = guard_tool_call(call("mcp__resend__send-email", {"to": ["delivered@resend.dev"]}))
    assert allowed


def test_cc_and_bcc_are_checked_too() -> None:
    allowed, reason = guard_tool_call(call("send-email", {"to": "delivered@resend.dev", "bcc": "boss@company.com"}))
    assert not allowed
    assert "boss@company.com" in reason


def test_batch_send_checks_every_email() -> None:
    emails = [{"to": "delivered@resend.dev"}, {"to": "x@gmail.com"}]
    allowed, _ = guard_tool_call(call("mcp__resend__send-batch-emails", {"emails": emails}))
    assert not allowed


def test_another_tool_is_allowed() -> None:
    allowed, _ = guard_tool_call(call("mcp__resend__list-emails", {}))
    assert allowed


def run_guard(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", "run", "mailroom", "guard"], input=payload, capture_output=True, text=True)


def test_guard_command_exits_2_for_gmail_with_reason_on_stderr() -> None:
    result = run_guard(call("mcp__resend__send-email", {"to": "sara.ali@gmail.com"}))
    assert result.returncode == 2
    assert "sara.ali@gmail.com" in result.stderr


def test_guard_command_exits_0_for_practice_address() -> None:
    result = run_guard(call("mcp__resend__send-email", {"to": "delivered@resend.dev"}))
    assert result.returncode == 0


def test_guard_command_exits_0_for_another_tool() -> None:
    assert run_guard(call("Read", {"file_path": "x"})).returncode == 0

"""Adapt mini-agent's complete message history to the same verification grader.

Call after agent_loop; completed must come from its 'done' event, not text.
This adapter does not run tools, modify the repository, or grade code correctness.
"""
from evalcourse.judge import evaluate


def judge_messages(messages, *, completed, call=None):
    pending, events, final = {}, [], ""
    for message in messages:
        if message["role"] == "assistant":
            calls = message.get("tool_calls") or []
            final = "" if calls else message.get("content") or ""
            for tool in calls:
                if tool["id"] in pending:
                    raise ValueError("Duplicate tool call identity")
                pending[tool["id"]] = tool["function"]
        elif message["role"] == "tool":
            tool = pending.pop(message["tool_call_id"])
            events.append({"kind": "tool", "name": tool["name"],
                           "arguments": tool["arguments"], "result": message["content"]})
    if pending:
        raise ValueError("Missing tool results; do not grade incomplete evidence")
    return evaluate({"status": "done" if completed else "incomplete", "final": final}, events, call)

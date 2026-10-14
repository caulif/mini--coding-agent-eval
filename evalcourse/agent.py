"""Ask -> tool -> observation -> ask. A deliberately small coding agent."""
import json
from .client import complete
from .grading import check


def schema(name, description, properties, required=None):
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties,
                           "required": list(properties) if required is None else required, "additionalProperties": False}}}


TOOLS = [schema("read", "Read solution.py and public test examples.", {}),
         schema("write", "Replace solution.py with Python source defining solve(value).",
                {"content": {"type": "string"}}),
         schema("test", "Run public examples, or 1-8 self-authored cases. Self-authored expectations are not an independent correctness oracle.",
                {"cases": {"type": "array", "minItems": 1, "maxItems": 8,
                           "items": {"type": "object", "properties": {"input": {}, "expected": {}},
                                     "required": ["input", "expected"], "additionalProperties": False}}}, [])]


def test_solution(source, public, args):
    if set(args) - {"cases"}:
        raise ValueError("Unknown test arguments")
    cases = args.get("cases", public)
    if "cases" in args:
        if not isinstance(cases, list) or not 1 <= len(cases) <= 8 or any(
                not isinstance(c, dict) or set(c) != {"input", "expected"} for c in cases):
            raise ValueError("Provide 1-8 input/expected pairs")
        if len(json.dumps(cases, allow_nan=False).encode("utf-8")) > 8192:
            raise ValueError("Custom cases exceed 8 KiB")
    return {**check(source, cases), "evidence_source": "agent_authored" if "cases" in args else "public",
            "cases": cases}


def run_agent(task, root, prompt, max_turns, emit, call=complete):
    messages = [{"role": "system", "content": prompt},
                {"role": "user", "content": task["prompt"]}]
    tokens, requests, tool_count = 0, 0, 0
    usage_known = True
    for turn in range(max_turns):
        emit("request", turn=turn + 1)
        response = call(messages, TOOLS)
        requests += 1
        usage = response.get("usage", {})
        total = usage.get("total_tokens")
        usage_known &= type(total) is int and total >= 0
        if type(total) is int and total >= 0:
            tokens += total
        message = response["choices"][0]["message"]
        messages.append(message)
        finish = response["choices"][0].get("finish_reason")
        emit("assistant", message=message, usage=usage, response_model=response.get("model"), finish_reason=finish)
        if finish in {"length", "content_filter"}:
            return {"status": "output_limit" if finish == "length" else "filtered",
                    "final": message.get("content") or "", "tokens": tokens if usage_known else None,
                    "requests": requests, "tools": tool_count}
        calls = message.get("tool_calls") or []
        if not calls:
            return {"status": "done", "final": message.get("content") or "",
                    "tokens": tokens if usage_known else None, "requests": requests, "tools": tool_count}
        if len(calls) > 8:
            raise ValueError("Too many tools in one response")
        for tool in calls:
            name = tool["function"]["name"]
            try:
                args = json.loads(tool["function"]["arguments"])
                if not isinstance(args, dict):
                    raise ValueError("Arguments must be an object")
                source = (root / "solution.py").read_text(encoding="utf-8")
                if name == "read" and not args:
                    result = {"source": source, "public_tests": task["public"]}
                elif name == "write" and set(args) == {"content"} and isinstance(args["content"], str):
                    (root / "solution.py").write_text(args["content"], encoding="utf-8")
                    result = "written"
                elif name == "test":
                    result = test_solution(source, task["public"], args)
                else:
                    raise ValueError("Unknown tool or invalid arguments")
            except (ValueError, OSError) as error:
                result = {"error": type(error).__name__}
            tool_count += 1
            emit("tool", id=tool["id"], name=name, arguments=tool["function"]["arguments"], result=result)
            messages.append({"role": "tool", "tool_call_id": tool["id"], "content": json.dumps(result, ensure_ascii=False)})
    return {"status": "budget", "final": "", "tokens": tokens if usage_known else None,
            "requests": requests, "tools": tool_count}

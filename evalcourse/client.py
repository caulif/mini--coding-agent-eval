"""One explicit Chat Completions request; no automatic retries."""
import json
import os
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Endpoint redirected; configure the final endpoint explicitly")


def complete(messages, tools=None, *, model=None):
    base = os.environ.get("EVAL_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    parsed = urlparse(base)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Endpoint must not contain credentials, query, or fragment")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}):
        raise ValueError("Use HTTPS (HTTP is allowed only for loopback tests)")
    payload = {"model": model or os.environ["EVAL_MODEL"], "messages": messages,
               "max_tokens": 2048, "temperature": 0}
    if tools:
        payload["tools"] = tools
    request = Request(base + "/chat/completions", json.dumps(payload).encode(),
                      {"Content-Type": "application/json",
                       "Authorization": "Bearer " + os.environ["EVAL_API_KEY"]})
    with build_opener(NoRedirect).open(request, timeout=30) as response:
        return json.load(response)

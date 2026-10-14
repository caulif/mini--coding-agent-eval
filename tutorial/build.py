"""Build standalone HTML using only Python's standard library."""
import argparse
import ast
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tutorial"
TITLES = ['Agent 评测基础', '评测的组成', '评测维度与粒度', '评分标准与 Grader 设计', '任务集与运行环境', '执行记录与失败分析', 'LLM Judge 的设计与验证', '可靠性与版本比较', 'Coding Agent 评测设计', '最小 Python Eval 实现', 'System Prompt A/B 实验', '持续评测与工程扩展']
EN_TITLES = ['Agent Evaluation Foundations', 'The Parts of an Evaluation', 'Dimensions and Granularity', 'Criteria and Grader Design', 'Tasks and Environments', 'Traces and Failure Analysis', 'LLM Judge Design and Validation', 'Reliability and Version Comparison', 'Coding Agent Experiment Design', 'A Minimal Python Eval Implementation', 'The System Prompt A/B Experiment', 'Continuous Evaluation and Engineering']


def localize(text, language):
    if language == "zh-CN":
        return text
    translations = {"复制": "Copy", "交付成功": "Successful deliveries", "真实实验的交付结果": "Recorded delivery results",
        "任务": "Task", "三次尝试": "Three trials", "版本": "Version", "通过 / 有效判定": "Passed / scored",
        "评审错误": "Judge errors", "跳过": "Skipped", "平均 Agent 耗时": "Mean agent time",
        "累计 Agent token": "Total agent tokens", "未知（有缺测）": "Unknown (missing usage)", " 秒": " s"}
    text = re.sub(r"第 (\d+) 次：", r"Trial \1: ", text)
    for original, translated in translations.items():
        text = text.replace(original, translated)
    return text



def include(match, language="zh-CN"):
    path, _, symbol = match[1].partition("#")
    code = (ROOT / path).read_text(encoding="utf-8")
    if symbol:
        node = next(n for n in ast.parse(code).body if getattr(n, "name", None) == symbol
                    or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == symbol for t in n.targets))
        code = "\n".join(code.splitlines()[node.lineno - 1:node.end_lineno]) + "\n"
    return f'<figure class="code"><figcaption><span>{html.escape(path + (" · " + symbol if symbol else ""))}</span><button type="button" class="copy">{localize("复制", language)}</button></figcaption><pre><code>{html.escape(code)}</code></pre></figure>'


def experiment(kind):
    directory = ROOT / "experiments/quixbugs-holdout-3"
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (directory / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    if kind == "outcome":
        cards = "".join(f'<div><span>Prompt {v}</span><strong>{r["successes"]}<small> / {r["trials"]}</small></strong><span>交付成功</span></div>' for v, r in report["versions"].items())
        return '<div class="result-cards" aria-label="真实实验的交付结果">' + cards + '</div>'
    if kind == "tasks":
        body = '<tr><th scope="col">任务</th><th scope="col">A · 三次尝试</th><th scope="col">B · 三次尝试</th></tr>'
        for task in report["per_task_delta"]:
            body += '<tr><th scope="row">' + html.escape(task) + '</th>'
            for version in ("A", "B"):
                selected = sorted((r for r in rows if r["task"] == task and r["version"] == version), key=lambda r:r["repeat"])
                marks = ''.join(f'<span class="trial-mark {"pass" if r["passed"] else "fail"}" title="第 {r["repeat"]+1} 次：{html.escape(r["status"])}">{"✓" if r["passed"] else "×"}</span>' for r in selected)
                body += f'<td>{marks} <span class="trial-count">{sum(r["passed"] for r in selected)}/3</span></td>'
            body += '</tr>'
    elif kind == "judge":
        body = '<tr><th>版本</th><th>通过 / 有效判定</th><th>评审错误</th><th>跳过</th></tr>'
        for version, r in report['versions'].items():
            j = r['judge']
            body += f'<tr><td>{version}</td><td>{j["passed"]} / {j["scored"]}</td><td>{j["errors"]}</td><td>{j["skipped"]}</td></tr>'
    elif kind == "cost":
        body = '<tr><th>版本</th><th>平均 Agent 耗时</th><th>累计 Agent token</th></tr>'
        for version, r in report['versions'].items():
            tokens = f'{r["total_tokens"]:,}' if r['total_tokens'] is not None else '未知（有缺测）'
            body += f'<tr><td>{version}</td><td>{r["mean_seconds"]:.2f} 秒</td><td>{tokens}</td></tr>'
    else:
        raise ValueError("Unknown experiment view")
    return '<div class="table"><table>' + body + '</table></div>'


def build(language="en"):
    if language not in ("en", "zh-CN"):
        raise ValueError("Unsupported language")
    source = SOURCE / "en" if language == "en" else SOURCE
    titles = EN_TITLES if language == "en" else TITLES
    stages = {1: "定义判断 · 01–04", 5: "建立可信测量 · 05–08", 9: "实现测量 · 09–10", 11: "作出判断 · 11–12"}
    if language == "en":
        stages = {1: "Define the decision · 01–04", 5: "Build the measurement · 05–08", 9: "Implement the design · 09–10", 11: "Interpret the evidence · 11–12"}
    chapters, navigation = [], []
    stage = ''
    for i, title in enumerate(titles, 1):
        if i in stages:
            stage = stages[i]
            navigation.append(f'<div class="nav-stage">{stage}</div>')
        body = (source / f"{i:02d}.html").read_text(encoding="utf-8")
        body = re.sub(r"\{\{code:([^}]+)\}\}", lambda m: include(m, language), body)
        body = re.sub(r"\{\{experiment:(\w+)\}\}", lambda m: localize(experiment(m[1]), language), body)
        sections = []
        def heading(match):
            anchor = f'ch{i}-s{len(sections)+1}'
            sections.append((anchor, match[1]))
            return f'<h3 id="{anchor}" tabindex="-1">{match[1]}</h3>'
        body = re.sub(r'<h3>(.*?)</h3>', heading, body)
        subnav = ''.join(f'<a href="#{anchor}">{label}</a>' for anchor,label in sections)
        navigation.append(f'<div class="nav-group"><a class="chapter-link" href="#ch{i}"><span>{i:02d}</span>{title}</a><div class="chapter-links">{subnav}</div></div>')
        onward = f'<a class="next-chapter" href="#ch{i+1}"><span>继续阅读 · {i+1:02d}</span><b>{titles[i]} →</b></a>' if i < 12 else '<a class="next-chapter" href="#top"><span>阅读完成</span><b>回到阅读路线 ↑</b></a>'
        if language == "en":
            onward = onward.replace("继续阅读", "Continue").replace("阅读完成", "End of article").replace("回到阅读路线", "Back to the overview")
        chapters.append(f'<section id="ch{i}" class="chapter" data-stage="{stage}" aria-labelledby="ch{i}-title"><div class="chapter-no">{stage} / {i:02d}</div><h2 id="ch{i}-title" tabindex="-1">{title}</h2>{body}{onward}</section>')
    nav = ''.join(navigation)
    count = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in (ROOT / "evalcourse").glob("*.py"))
    page = (source / "layout.html").read_text(encoding="utf-8")
    for key, value in {"STYLE": (SOURCE / "style.css").read_text(encoding="utf-8"), "SCRIPT": (SOURCE / "app.js").read_text(encoding="utf-8"), "NAV": nav, "CHAPTERS": "\n".join(chapters), "LINES": str(count)}.items():
        page = page.replace("{{" + key + "}}", value)
    if "{{" in page:
        raise ValueError("Unexpanded source marker")
    return page


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for language, filename in (("en", "guide.html"), ("zh-CN", "guide.zh-CN.html")):
        page = build(language)
        target = ROOT / filename
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != page:
                raise SystemExit(f"{filename} is stale; run python tutorial/build.py")
            print(f"{filename} matches its sources and executable code.")
        else:
            target.write_text(page, encoding="utf-8", newline="\n")
            print(target)

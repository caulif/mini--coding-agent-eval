# mini coding agent eval

[English](README.md) | **简体中文**

一次从概念、实现到真实实验的 Agent 评测探索。

**改了 coding agent 的 system prompt，它真的更会修代码了吗？** 我想用一个足够小、又能保留真实问题的项目，认真回答这个问题。从确定评测目标、构建任务集，到组合程序评分与 LLM judge，再到比较两版 prompt，这里记录了我的理解、设计选择和实验结果。

当前实验没有观察到新 prompt 的修复收益，却暴露了响应预算、验证声明和评审缺测等问题。这些发现也是下一轮改进的起点。代码和原始记录一并公开，便于复核和讨论。

文章提供默认英文的 [English HTML](guide.html)、[中文 HTML](guide.zh-CN.html)，依次展开概念、实验设计、实现和结果分析。

## 设计选择

- 8 道固定版本的 QuixBugs 算法修复题，3 dev / 5 holdout；原始代码、MIT 许可、参考修复、独立预期与错误修复检查可追溯。
- 同一最小 coding agent 使用 read / write / test。test() 跑公开示例，test(cases=...) 支持 1–8 个小型自建用例；两版 prompt 工具完全一致。
- 每次新目录。最终验收重跑独立用例；自建预期只作为反馈，不替代验收。
- 主成功口径为功能通过且正常结束；可选 LLM judge 单独判断验证声明，保存依据、错误和消耗。
- A/B 按 task/repeat 配对交错；所有计划尝试保留，不为得到预想结论择优重跑。

这些是公开算法基准的实验适配，不是工业仓库 issue。任务来源不保证难度或训练未知，结论须带上任务与运行条件。

## 开始阅读

- 想理解评测：下载或克隆仓库后打开 [中文文章](guide.zh-CN.html)，可在顶部切换英文。
- 想获得完整排版：下载或克隆仓库后，用浏览器打开 `guide.zh-CN.html`。GitHub 文件页展示的是源码，目前没有已发布的在线站点。
- 想看实际结论：阅读 [真实实验解读](experiments/quixbugs-holdout-3/analysis.md)。

## 运行与复核

在项目根目录使用 Python 3.12（当前支持并验证的版本）。运行代码只依赖标准库。

**检查评分器的区分能力（无需模型）**

```sh
python -m examples.inspect_grader
```

预期输出：

```text
starter {'target': False, 'regression': False}
reference {'target': True, 'regression': True}
one-item-only {'target': False, 'regression': False}
```

同一道真实 knapsack 任务中，缺陷程序和“只挑一个物品”的错误修复被拒绝，参考修复通过。这验证了这些用例的区分能力，还不是 agent 的能力评测。

**复核已有实验（无需模型）**

```sh
python -m examples.verify_experiment
```

检查计划排程、任务快照哈希、逐次结果、评分记录及报告数值的一致性，并重新汇总 A=15/15、B=13/15。B 的两次未交付分别为 `output_limit` 和 `agent_error`，未知用量仍为未知。命令只读文件，不执行候选代码，不调用模型、不改写原记录。

当前代码与实验冻结版本有差异时会列出文件名；例如报告后来增加了结束状态计数，不意味着原 agent 使用了新代码。此入口检查记录内部一致性，不证明历史响应的真实性，也不重新验证候选代码。

**用自己的模型运行单题 A/B**

候选 Python 会在宿主子进程执行，**这不是安全沙箱**。请在无敏感数据的受限环境中运行模型生成的代码；临时目录和超时不能阻止任意 Python 访问宿主。详见下方执行边界。

模型需兼容 Chat Completions 与 function tools。PowerShell 示例：

```powershell
$env:EVAL_BASE_URL = 'https://your-provider.example/v1'
$env:EVAL_MODEL = 'your-model'
# Set EVAL_API_KEY securely in the current environment; do not commit it.
python -m evalcourse.run --split dev --tasks knapsack --repeats 1 --judge --out runs/first-pair
```

这会运行 A/B 各一次，最多 12 次 agent 请求和 2 次 judge 请求；实际计费以供应商为准。完成后打开 `runs/first-pair/report.md`，再根据其中的结束状态查看各次 `result.json`、`solution.py` 和 `trace.jsonl`。真实结果可能与仓库记录不同，不要求两版都成功。

## 完整实验与检查

```sh
python -m unittest discover -s tests -v
python tutorial/build.py --check
python -m evalcourse.run --split dev --repeats 1 --judge --out runs/dev-check
python -m evalcourse.run --split holdout --repeats 3 --judge --out runs/holdout-check
```

后两条需要上述模型配置。输出目录必须不存在。支持 `--tasks`、`--turns`、`--seed`；默认 dev、3 次重复、6 轮、seed 0。客户端固定 temperature 0、每响应最多 2048 token、30 秒请求超时、无自动重试。`--judge` 开启声明评分；`EVAL_JUDGE_MODEL` 可另选模型，默认与 agent 相同。报告记录 token，不估算未确认的价格。

复核已有记录与重新实验是两件事：更换模型、服务端版本或预算都会改变条件；同名模型也不保证重现同样的结果。新运行单独留档，不覆盖仓库中的实验。

## 输出与解释

每个批次保存 manifest（配置、排程、prompt、哈希）、任务快照、results.jsonl、report.json/report.md；每次运行保存 trace.jsonl、solution.py、result.json。

- `functional_pass`：目标及回归验收全部通过。
- `passed`：functional_pass 且 `status == done`。
- `termination_counts`：每种 agent 结束状态的次数。`done` 不保证功能通过；`budget` 是轮次耗尽，`output_limit` 是响应额度耗尽，`agent_error` 是请求或执行异常，`filtered` 表示供应商内容过滤。
- `judge.status`：ok / error / skipped；只有 ok 进入声明判定分母，错误与跳过独立呈现。
- agent 与 judge 的 token、时间分开统计；缺少 token usage 时保留未知，不填写零。
- any/all 是经验上的至少一次/全部成功任务比例。任务 bootstrap 为小样本描述，不等于普遍能力或等效性证据。

复用已有轨迹评分，不再运行 agent：

```sh
python -m evalcourse.rejudge runs/holdout-check --out runs/claims-check
```

rejudge 先检查源批次完整性，再写新目录。它保存源文件哈希；若看结果后修改 rubric，需标为探索性分析。

## 实验与任务

- [实验协议](experiments/PROTOCOL.md)：预先固定的假设、预算、主辅指标与解释规则。
- [任务构建](data/README.md)：来源、输入域、独立 oracle、错误修复和排除理由。
- 开发试跑：`experiments/quixbugs-dev-1/`。
- 最终 A/B：`experiments/quixbugs-holdout-3/`，5 题 × 2 版 × 3 次。
- 事后补测：`experiments/quixbugs-missing-followup-1/`，独立保留，不回填主实验。

公开基准可能被模型见过；holdout 只表示本次没有用于调 prompt。声明 judge 未经独立人工标注校准，结果作为辅助诊断，不能直接当成可靠质量排名。

本轮最终结果：A **15/15**、B **13/15**，未观察到 B 的功能修复收益；B 的两次未交付分别是输出上限停止和首次请求异常。详细归因、声明 judge 覆盖与成本缺测见 [真实实验解读](experiments/quixbugs-holdout-3/analysis.md)。

## 代码结构

```text
evalcourse/     client / agent / grading / judge / run / report / rejudge
data/           上游原始程序、许可、来源及任务生成器
tasks.json      当前八题及公开/独立验收
prompts/        A、B 两版 system prompt
tests/          运行器、评分器、任务质量与协议检查
examples/       mini-agent 消息到声明 judge 的最小适配
tutorial/       中英文 HTML 源文、样式和构建器
experiments/    预定协议及不可覆盖的真实记录
```

我把规模作为设计约束：实现保持小到能够完整阅读，同时保留任务、轨迹、评分和实验比较这些必要部分。页面中的核心行数由构建器统计，包含 evalcourse 下的运行、评分、汇总与重评代码，不包含任务资产、测试和文稿。

## 文章维护

中文源文位于 `tutorial/01.html` 至 `12.html`，英文源文位于 `tutorial/en/`。修改对应内容与 layout 后执行 `python tutorial/build.py`，同时生成默认英文的 `guide.html` 和中文的 `guide.zh-CN.html`。两版通过顶部链接切换；启用 JavaScript 时保留章节位置。代码块从实际 Python 函数提取，实验表格从持久化报告生成。

维护与发布检查见 [贡献指南](CONTRIBUTING.zh-CN.md)。

## 执行边界

候选代码是 Python，评分子进程不是安全沙箱。临时目录、超时与环境变量清理仅提供复位和故障控制；请只用于当前受控任务。不要直接接入陌生代码、私人仓库或宿主敏感目录。扩展到真实仓库前先采用受限执行环境。

原创文章与代码为 MIT，第三方程序遵循附带许可。见 [来源说明](THIRD_PARTY_NOTICES.md) 和 [贡献指南](CONTRIBUTING.md)。

代码注释与文档字符串统一使用英文。中文界面文本、原始任务 prompt 和模型记录属于内容或实验数据，保留原语言；翻译任务会改变实验条件。

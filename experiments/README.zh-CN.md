# 实验记录

原始批次保留全部计划尝试。复核只读已有证据；重新运行和事后评审另建目录，不用后来成功的尝试覆盖原失败。

| 记录 | 用途 | 是否进入文章当前主结论 |
| --- | --- | --- |
| [quixbugs-dev-1](quixbugs-dev-1/report.md) | 3 道开发题，A/B 各一次，检查运行链路 | 否 |
| [quixbugs-holdout-3](quixbugs-holdout-3/analysis.md) | 5 道最终题，A/B 各三次，共 30 次 | 是：A 15/15，B 13/15 |
| [quixbugs-missing-followup-1](quixbugs-missing-followup-1/README.md) | 原缺测的事后单次补测，独立留档 | 否，不回填原分母、成本或缺测 |

## 复核当前实验

在仓库根目录运行 `python -m examples.verify_experiment`。无需 API key，不发模型请求，也不执行候选程序。它检查记录的一致性，并从原始行重算报告，保留缺测、失败和未知用量。

[预定协议](PROTOCOL.md) 固定假设、模型、预算和分母；[任务集说明](../data/README.md) 解释来源与适配。原始批次的 manifest 保存实际条件，源码哈希用于识别版本变化，不等于归档了可恢复的历史源码。

## 当前证据的范围

本次最终集已经运行真实模型。A 为 15/15，B 为 13/15；B 的两次未交付分别是响应截断和首次请求 HTTPError。主结果没有显示 B 的修复交付收益。缺测与异常保留用于后续设计反馈，不靠选择性补跑改写结论。

公开算法题可能被模型见过；holdout 只表示未用于本次 prompt 开发。模型响应名、token 与结束状态保存在轨迹中。耗时依赖机器和网络，token 不等于账单金额；judge 尚无独立人工校准。

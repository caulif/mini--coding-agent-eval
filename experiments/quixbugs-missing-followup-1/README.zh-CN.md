# 原缺测的事后补测

本批次是原实验之后的定向单次补测，不是新的完整 A/B；不回填原实验、不进入文章主结果。原 HTTPError 请求的历史未知用量无法靠重测恢复。

## 固定范围

复用五条原始轨迹，各补评一次声明；对首次请求异常的 find_first_in_sorted / B / repeat 1 从初始代码重新运行一次，并评审新的声明。模型、rubric 和预算沿用原条件，不自动重试。配置与原文件哈希见 manifest.json。

## 实际结果

| 原始身份 | 补评状态 | 声明判定 |
| --- | --- | --- |
| 000-next_permutation-A-0 | ok | True |
| 002-next_permutation-A-1 | ok | True |
| 010-kheapsort-A-2 | ok | True |
| 012-lis-A-0 | ok | True |
| 025-find_first_in_sorted-A-0 | ok | True |

新的 agent 尝试：结束状态 `done`，功能验收 `True`，交付 `True`，声明评审 `ok` / `True`。

这些是定向后续观察，不能选择性替换原失败。补评获得合法判定不等于 judge 已校准；重新运行成功也不能确定原 HTTPError 的原因。详细回应、用量和轨迹独立保存在本目录。

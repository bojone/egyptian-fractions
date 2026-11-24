# 88 项局部构造实验源码

**中文 | [English](README.en.md)**

本目录保存围绕已知 89 项表示开展的局部构造搜索。它们用于分析具体变换族，**不提供全局 88 项排除，也不改变 $`87\le S(5)\le89`$ 的结论**。

## 实验源码与用途

- `audit89_pair_triple_merges.py`：穷举原集合全部 3916 个 pair 和 113564 个 triple 的直接合并；重复分母另计并排除。
- `search88_base_pair_swaps.py`：把 83 个基础分母中的每一对替换为两个互异单位分母，完整检查 3403 对。
- `search88_split_merge_neighbors.py`：一次拆分加一次合并邻居，359 个拆分候选、238 个状态。
- `search88_two_split_neighbors.py`：两个不同原始分母分别拆分，再做两次合并，60487 个拆分操作对。
- `search88_sequential_split_neighbors.py`：原始拆分后对新分母再次拆分，执行 7984 次连续拆分。
- `search88_three_to_two_divisors.py`：三项换两项的因数分解路径及候选宽度分析。
- `search88_three_to_two_costed.py`：按搜索代价组织三项换两项候选。
- `search88_local_replacements.py`：通用两项尾求解和优先局部替换。
- `search88_four_to_three.py`、`search88_four_to_three_independent.py`、`search88_five_to_four_independent.py`、`search88_six_to_five_independent.py`、`search88_six_to_five_independent_resume.py`、`search88_six_to_five_factor_tail.py`：更多受限变换实验。
- `search88_pair_driver.py`、`search88_variant_driver.py`、`search88_walk.py`：调度、变体驱动及随机游走参考实现。
- `search88_final_triple_regression.py`：专用三项尾可执行文件的结果回归。
- `scheduler_snapshot.py`：原调度环境的进程快照辅助程序。
- `verify.py`：原独立表示验证器副本。

这些源码保存了实际实验所使用的算法和输出字段，便于审查，而不是只保留最终“没有找到”的结论。

## 运行环境与限制

纯 Python 算法主要使用标准库和系统 `factor` 命令。部分专用尾项程序还依赖原生产二进制、owner 管理或调度进程；这些依赖没有全部纳入精简包。特别是 `search88_final_triple_regression.py` 需要原 `search88_final_triple` 可执行文件，缺少它时不能将运行失败当成负结果。

`production/construct88/logs` 是指向 `../logs` 的相对软链接，便于查看正式证据。若直接在该目录运行，某些输出文件已经存在，脚本会有意停止以避免覆盖历史证据。**运行实验时必须使用新的空工作目录。**

## 在新空目录重跑

以下命令在项目根目录执行，创建独立工作区，不修改随包日志：

```bash
tmp=$(mktemp -d)
cp production/construct88/*.py "$tmp/"
mkdir -p "$tmp/logs"
cp logs/construct89_emath.json "$tmp/logs/"
cd "$tmp"

python3 audit89_pair_triple_merges.py
python3 search88_base_pair_swaps.py
python3 search88_split_merge_neighbors.py
python3 search88_two_split_neighbors.py
python3 search88_sequential_split_neighbors.py
```

每个脚本会在新工作区的 `logs/` 写入对应报告。若发现候选，程序会另做精确有理数验证；重复分母仍需额外检查总和，不能因为项数减少就接受。

`search88_three_to_two_costed.py`、`search88_local_replacements.py` 和其他变体可按相同方式复制到新目录后运行。需要专用二进制或调度器的脚本应先补齐原环境，不能期待在当前精选包中直接完成全量搜索。

## 验证记录

[logs/construct88_source_rechecks.json](../../logs/construct88_source_rechecks.json) 汇总独立空目录中的源码重跑结果，逐项核对：

- pair/triple 数量及 58、214 个重复分母；
- 3403 个基础分母对全部只返回原集合；
- 359/238 个一次拆分候选和状态；
- 60487 个两次拆分操作对和 25885 个状态；
- 7984 次连续拆分和 7913 个状态；
- 所有报告均为局部范围且没有新表示。

另有两个标准库独立检查位于 `src/audit_merges89.py` 和 `src/audit_base_pairs89.py`，可用 `make audit-merges` 执行。原始局部审计 JSON 位于 `logs/search88_*.json`、`logs/audit89_pair_triple_merges.json` 和 `logs/construct88_tail60_complete_audit.json`。

## 证据边界

这些实验只排除已命名的局部变换或指定构造族。它们不能证明所有 88 项表示不存在，也不能替代完整 87 项排除。更广泛的完整搜索应使用 `production/fixed_server` 与原始完整任务、owner 和覆盖体系。

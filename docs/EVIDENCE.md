# 证据索引、验证层级与发布边界

**中文 | [English](EVIDENCE.en.md)**

本发布保留能够独立复核的精选证据，而不是把庞大的工作目录原样打包。以下说明每份文件支持什么结论、不能支持什么结论，以及为什么没有把它们误认为 $`S(5)`$ 的定值证明。

## 1. 一页结果摘要

最直接的机器可读入口是 [logs/current_result_summary.json](../logs/current_result_summary.json)，包含：

- $`S(1)=1,S(2)=4,S(3)=13,S(4)=33`$；
- $`87\le S(5)\le89`$，且精确值未定；
- safe31700 的 276997 份验收日志、3109 个未覆盖父分支及分层计数；
- 快照、独立覆盖、未闭合清单和 89 项表示的路径与哈希；
- 历史负日志计数和四个尚未完成的 $`r=4`$ 坐标；
- 未发现 87 或 88 项表示、未宣称全局排除。

`src/audit_release.py` 重新检查这些核心字段，而不是仅信任该摘要。

## 2. 显式表示及小值证据

| 文件 | 内容 | 独立验证方式 |
|---|---|---|
| [logs/construct89_emath.json](../logs/construct89_emath.json) | 89 项分母、构造定义、出处、验证字段 | 重建集合，检查互异性并用 `Fraction` 求和为 5 |
| [logs/small_cases.log](../logs/small_cases.log) | 3、4 的小值穷举及 5 的 83/84 项记录 | `make selftest` 重跑核心案例 |
| [logs/revalidated_small/](../logs/revalidated_small/) | 小值独立复验输出 | 与本次新构建输出对照 |
| [src/bounds.py](../src/bounds.py) | 调和级数界和 3、4 的表示 | 直接执行，精确有理数计算 |
| [src/verify.py](../src/verify.py) | 通用分母列表验证器 | `python3 src/verify.py N ...` |
| [logs/coverage85_cpu_only.log](../logs/coverage85_cpu_only.log) | 85 项纯 CPU 完整覆盖 | 检查 `uncovered branches: 0` 和空正例集合 |
| [logs/r9_depth4_complete_coverage86.log](../logs/r9_depth4_complete_coverage86.log) | 86 项最终完整覆盖 | 检查零未覆盖及空正例集合 |
| [logs/r9_depth4_complete_audit.log](../logs/r9_depth4_complete_audit.log) | 86 项收尾审计 | 核对 118/118 子项、9/9 父分支和零失败 |

3 的 12 项和 4 的 31、32 项完整排除共同给出 $`S(3)\ge13`$、$`S(4)\ge33`$；对应的 13、33 项表示给出匹配上界。5 的 83、84、85、86 项完整排除则给出 $`S(5)\ge87`$。较小项数已由调和级数界排除，所以“不超过 86 项无解”是完整结论。

这些文件不包含 87 或 88 项的完整覆盖，因此不能把同样的逻辑延伸到 89 的最少性。

## 3. safe31700 核心认证文件

| 文件 | 关键内容 |
|---|---|
| [logs/independent_safe31700_audit.json](../logs/independent_safe31700_audit.json) | 独立全量内容哈希审计、owner 摘要、无缓存覆盖结果 |
| [logs/independent_safe31700_coverage.log](../logs/independent_safe31700_coverage.log) | 独立重建的分层覆盖和总计 |
| [logs/production_safe31700_3109.json](../logs/production_safe31700_3109.json) | 生产快照、分层计数、相关审计链接 |
| [logs/goal87_safe31700.log](../logs/goal87_safe31700.log) | 生产全局覆盖输出 |
| [logs/uncovered_parents_safe31700.json](../logs/uncovered_parents_safe31700.json) | 全部 3109 个未闭合坐标及十个来源文件哈希 |
| [logs/uncovered_inventory_safe31700_driver.log](../logs/uncovered_inventory_safe31700_driver.log) | 清单生成结果及自身 SHA-256 |

主要标识为：

- 生产快照 SHA-256：`4b3deb581f3113b6792c21ab1f872d1a75042ce01251ff9e50013933c10eb161`；
- 独立覆盖 SHA-256：`662f00c6942ba7138c468f50177eb1309c3f43937d6a83692b00ddc11f830038`；
- 未闭合清单 SHA-256：`babdf43f726ab5e057cc5295f27a616e3a6a7f4a4c9bc8653cf9f13b9aab37f7`。

独立审计字段 `full_content_hash_audit: true`、`coverage_cache_used: false` 和 `independent_coverage_reused_after_completed_run: false` 表明当次复核重新计算内容哈希并重建覆盖，而不是复用先前独立覆盖。

`verified_safe_logs` 与 `unique_verified_log_paths` 都为 276997。另有 1672 份并发日志在独立覆盖时仍未验收，未计入证明。未覆盖返回码 1 表示部分覆盖，不是全局无解。

## 4. 十层未闭合来源

清单不是只有总数的黑箱。每层都有原始 `uncovered_parent` 坐标，发布审计重新解析并比较集合：

| 层 | 数量 | 来源文件 |
|---|---:|---|
| $`r=4`$ | 14 | `logs/remaining_r4_safe31700.log` |
| $`r=5`$ | 155 | `logs/remaining_r5_safe31700.log` |
| $`r=6`$ | 338 | `logs/r6_scoped_coverage_safe30060.log` |
| $`r=7`$ | 386 | `logs/r7_scoped_coverage_safe23500.log` |
| $`r=8`$ | 658 | `logs/r8_scoped_coverage_safe31680.log` |
| $`r=9`$ | 574 | `logs/r9_scoped_coverage_safe31310.log` |
| $`r=10`$ | 436 | `logs/r10_scoped_coverage_safe31530.log` |
| $`r=11`$ | 314 | `logs/r11_scoped_coverage_safe31700.log` |
| $`r=12`$ | 207 | `logs/r12_scoped_coverage_safe31640.log` |
| $`r=13`$ | 27 | `logs/remaining_r13_safe31700.log` |

后续没有闭合的层沿用最近已认证的分层日志；新闭合层使用新日志。各层合并后坐标互异且有序，总数 3109。清单的 scope 明确写着 **not a negative certificate**，即这些分支尚未被排除。

safe31990 另有独立的 **3101 个坐标清单**：[logs/uncovered_parents_safe31990.json](../logs/uncovered_parents_safe31990.json)，SHA-256 为 `26862c51260a3e627fab4760dbc05badebc97613aa424dd2b598a7678111ba07`。其中 r9、r10、r11、r12 分别改用 safe31940、safe31980、safe31970、safe31990 的最新分层日志，其余层沿用前述未变化的认证日志。两份清单分别保留，不混用。

## 5. 最近一个完整闭合示例

[logs/r11_x51_y75_closure_safe31700.json](../logs/r11_x51_y75_closure_safe31700.json) 给出 $`(11,51,75)`$ 的闭合。所需子坐标恰为 $`z=76,77,78,79`$，对应四份原始日志：

```text
logs/fixed87_depth3/r11_x51_y75_z76.log
logs/fixed87_depth3/r11_x51_y75_z77.log
logs/fixed87_depth3/r11_x51_y75_z78.log
logs/fixed87_depth3/r11_x51_y75_z79.log
```

发布审计对每份日志检查完整 SHA-256、`result=no`、无 `result=yes`、无 `MULTISLOT ` 和安全引擎标签，并检查前后集合关系：原先 315 个未覆盖父分支，之后 314 个，差集只有 $`(11,51,75)`$。

其他相关文件为：

- `logs/r11_scoped_coverage_safe31580.log`：闭合前集合；
- `logs/r11_scoped_coverage_safe31700.log`：原闭合后集合，SHA-256 为 `ba10beefff8e72e2516f9b1da6c724587ce5b4e10cd83063b87fa8542ee07814`；
- `logs/r11_scoped_coverage_safe31700_recheck.log`：独立复核集合，SHA-256 为 `e4ecb17b7ce4931584126b9ee420c7066c4e4f7d3041da356955f890d2c062ef`；
- `logs/r11_closures_safe31700_recheck.json`：差分程序复核结果；
- `logs/r11_new_closures_safe31700_summary.json`：闭合摘要及完整 z 区间。

原覆盖和复核覆盖的文件哈希不同，但 314 个未闭合坐标集合完全相同。这是允许并发统计变化的正确比较方式，不能仅凭哈希不同否定覆盖，也不能仅凭汇总计数相同就跳过集合比较。

这个例子展示了局部闭合需要哪些证据。它只减少一个父分支，并不证明其他 3109 个分支。

## 6. 历史审计摘要

原始历史审计包含过时的硬件标识和大量二进制元数据，故本发布不原样收录。保留以下不含具体型号的数学摘要：

- [logs/history_safe31700_summary.json](../logs/history_safe31700_summary.json)：计数、零违规、零正例、原始审计 SHA-256、固定输入哈希和待处理坐标；
- [logs/two_tail_history_safe31700_validation.json](../logs/two_tail_history_safe31700_validation.json)：固定输入保存与恢复、归档顺序、计数和 r4 状态。

对应计数为：

| 目标 | 三层负日志 | 四层负日志 |
|---|---:|---:|
| 86 项 | 236879 | 206 |
| 87 项 | 397278 | 97 |

违规和正例均为空。原始历史审计 SHA-256 为 `ce48b523f25d7c73d99d940666e58725b45a95c885945c071602d0bc91811362`，固定输入 SHA-256 为 `cb42888b4e35c56dfa7a849645639c37e6ff9d20d21a5b488a36efa403953413`。四个模余 $`r=4`$ 坐标仍无终端负结果，不得据此排除。

历史审计只处理指定旧回退缺陷，不代替覆盖，也不自动追认其他历史实现。原始文件未被修改；本包只是选择不复制它们，并另存数学摘要。

## 7. 算法回归与 smoke 文件

- [logs/two_tail_complete_regression.log](../logs/two_tail_complete_regression.log)：完整回退正/负例及快速路径一致性结果。
- [logs/two_tail_forced_fallback_summary.json](../logs/two_tail_forced_fallback_summary.json)：强制 GPU 失败后 CPU 完整回退的正负例摘要；原始绝对路径不收录，保留原日志 SHA-256。
- [logs/three_pair_ratio_host_test.log](../logs/three_pair_ratio_host_test.log) 与 [logs/three_pair_ratio_regression.log](../logs/three_pair_ratio_regression.log)：三项尾主机回归、2404 个 GPU 任务及 655 个正例的原始输出。
- [logs/pruning_regression_summary.json](../logs/pruning_regression_summary.json)：三项尾剪枝的辅助回归摘要，明确性能采样不是覆盖证明。
- [logs/pigeonhole_product_fixed_regression.json](../logs/pigeonhole_product_fixed_regression.json)：修正乘积下界的独立划分检查摘要。
- [logs/product_max_server_smoke.json](../logs/product_max_server_smoke.json)：混合实现的基本 smoke 表示，明确 `coverage_accepted: false`。

这些文件用于解释实现和回归范围，不能单独支持全局最少性。

## 8. 发布包没有包含什么

本发布不包含：

- 全部 276997 份原始负日志和其他历史日志；
- 全部 owner 报告、完整生产连续文件及缓存；
- 全部历史二进制、具体硬件信息和退休进程现场；
- 大量未通过验收的候选、超时、暂停或性能实验输出。

因此，某些归档 JSON 中仍保留了指向原始完整数据环境的相对路径。这些路径用于溯源，**并不承诺所有被引用文件都包含在精简包中**。`src/audit_release.py` 只要求本说明列出的精选文件，不假装解析缺失数据。

生产脚本如 `audit_safe_snapshot.py`、`coverage87_distinct_v1.py` 和 `certify_coverage_delta.py` 供原始完整数据环境使用。它们需要完整 owner 记录、原始日志、二进制和部分历史进程信息，不能直接在本精简包上完成全量重算。`production/logs` 只是指向精选 `logs/` 的相对软链接，不是完整数据目录。

这是有意的发布边界：小值可以从零重跑，精选证据可以独立核验，完整大规模搜索则须使用原始完整证据或重新计算。

## 9. 校验和与复核顺序

建议按以下顺序复核：

```bash
# 1. 检查常规文件传输完整性
sha256sum -c SHA256SUMS

# 2. 独立审计随包证据
make audit

# 3. 构建并实际重跑小值
make selftest

# 4. 可选：构建混合实现并执行 smoke
make production-smoke NVCC=/path/to/nvcc GPU_POOL=1
```

修改文档或源码后，可执行 `make checksums` 重新生成清单。清单不包含本地构建的二进制、临时文件、软链接或 `results/validation/` 输出。`make clean` 不删除证据。

## 10. 88 项局部构造证据

为避免只凭一段文字概括局部搜索，发布包还保留了 17 份局部审计 JSON，覆盖指定基底删除、尾部家族、直接合并、三项换两项、拆分合并邻居、基础分母对交换和优先 pair90 家族。每份都明确 `global_88_nonexistence_claimed: false`，不能外推为全局无解。

可直接独立重跑两类检查：

```bash
python3 src/audit_merges89.py
python3 src/audit_base_pairs89.py
```

- [logs/merge89_independent_recheck.json](../logs/merge89_independent_recheck.json)：全部 3916 个 pair 和 113564 个 triple。58 个 pair、214 个 triple 的合并分母与原集合重复，精确求和不再为 5，必须拒绝；合法 88、87 项合并均为空。
- [logs/base_pairs89_independent_recheck.json](../logs/base_pairs89_independent_recheck.json)：全部 3403 个基础分母对，3403 个两项解都只返回原 89 项集合，没有新的 89 项状态。
- [logs/audit89_pair_triple_merges.json](../logs/audit89_pair_triple_merges.json) 与 [logs/search88_base_pair_swaps_independent.json](../logs/search88_base_pair_swaps_independent.json)：相应的原始局部审计及独立复核。

**重复分母不是合法解的捷径。** 合并后除了要求分母互异，还必须重新检查总和；若合并分母已存在，直接去重会改变总和。不能用“合并后项数变少”代替等式验证。

`make audit-merges` 会重新执行上述两个独立程序，`make check` 也已包含它们。其余局部家族保留原始审计文件，随包审计核对其有效标志、局部范围和空正例集合，**不声称重新执行了全部历史构造搜索**。实验源码及独立空目录运行方式见 [production/construct88/README.md](../production/construct88/README.md)，五组源码重跑的逐项核对摘要见 [logs/construct88_source_rechecks.json](../logs/construct88_source_rechecks.json)。局部证据只说明已命名构造族没有表示，不影响全局 $`87\le S(5)\le89`$ 的表述。

## 11. 结论的准确表述

本包支持以下严格结论：
$$S(1)=1,\quad S(2)=4,\quad S(3)=13,\quad S(4)=33,\qquad87\le S(5)\le89.$$

safe31700 是 $`k=87`$ 的部分覆盖认证点，不是 87 项排除；88 项的局部构造族检查也不是全局排除。若后续要证明 $`S(5)=89`$，必须分别完成两种全局排除，或至少找到一种 87 或 88 项表示以改变上界。

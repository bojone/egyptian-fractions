# 互异单位分数：精确搜索、证明与精选证据

**中文 | [English](README.en.md)**

**整个项目完全由 Kimi K3.1 Pro [thinkg: max] + Kimi-Code 自主完成。**

本项目研究这样的问题：对正整数 $`n`$，把
`$$n=\sum_{i=1}^{k}\frac1{a_i},\qquad a_i\in\mathbb Z_{>0},$$`
其中所有 $`a_i`$ 两两不同，所需的最少项数 $`k`$ 记为 $`S(n)`$。允许 $`1/1`$。本项目提供可执行源码、独立有理数验证器、完整小值穷举、精选覆盖证据和当前未完成工作的准确边界。

## 首先阅读：结论边界

| 项目 | 已证明结论 | 证据等级 |
|---|---:|---|
| $`S(1)`$ | $`1`$ | 显然 |
| $`S(2)`$ | $`4`$ | 三项和至多 $`11/6<2`$ |
| $`S(3)`$ | $`13`$ | 12 项完整穷举排除；13 项显式表示 |
| $`S(4)`$ | $`33`$ | 31、32 项完整穷举排除；33 项显式表示 |
| $`S(5)`$ | $`87\le S(5)\le89`$ | 不超过 86 项已完整排除；89 项表示已验证 |

**$`S(5)`$ 的精确值尚未确定。** 87 项和 88 项都必须分别处理：找到其中一种表示会改进上界，完整排除其中一种会改进下界；两类都排除才能证明 $`S(5)=89`$。局部父分支闭合、某个启发式构造族无解或硬件运行结束都不是全局最少性证明。

本发布采用 **safe31700** 作为 $`k=87`$ 的冻结认证点。该点有 276997 份验收负日志和 3109 个未覆盖父分支，不是 87 项无解的证明。结果总入口为 [logs/current_result_summary.json](logs/current_result_summary.json)。后续 **safe31990** 独立复核已推进到 277076 份验收日志、3101 个未覆盖父分支；日历跨度、单项耗时、最新分层和无法给出完工时间的原因见 [搜索历程与时间口径](docs/CAMPAIGN.md)。

## 快速开始

### 无需 GPU：审计精选证据

只需要 Python 3 和标准库：

```bash
make audit
```

成功时末尾输出：

```text
PASS: no specific hardware models or personal machine paths in the curated release
RELEASE_AUDIT_OK
```

这个命令会：

- 重新计算 3、4 的显式表示和 5 的 89 项表示的精确有理数和；
- 重算调和级数界及对称差的最大删除层数；
- 检查 85、86 项最终覆盖记录和 86 项收尾审计；
- 核对 safe31700 的审计字段、快照哈希、276997 份验收日志的计数及 3109 个未覆盖父分支；
- 逐个重建全部 3109 个未闭合坐标，并核对十层来源文件的集合及 SHA-256；
- 核对历史审计摘要、固定输入恢复记录和四个仍未完成的 $`r=4`$ 坐标；
- 对最近一个 $`r=11`$ 闭合逐条检查四份原始负日志及前后父分支集合；
- 检查发布文件中没有具体硬件型号或个人机器路径。

**它没有重新读取原始全部 276997 份日志，也没有从零重扫 85、86 或 87 项。** 它是对随包证据的独立一致性审计。完整搜索的最少性仍依赖原始搜索算法、完整历史证据和覆盖推导。详见 [docs/EVIDENCE.md](docs/EVIDENCE.md)。

### GMP 构建及小值实际穷举

需要 C++17 编译器和 GMP。默认链接参数为 `GMP_LIBS=-l:libgmp.so.10`；若系统库布局不同，可执行 `make selftest GMP_LIBS='-L/path/to/gmp/lib -lgmp'` 覆盖，不把本机链接方式当成跨平台保证：

```bash
make selftest
```

该命令编译 `src/symdiff_exact`，然后实际完成：

```text
PASS: no 11-term representation of 3 (complete r=1..2)
PASS: no 12-term representation of 3 (complete r=1..3)
PASS: independently verified a 13-term representation of 3
PASS: no 31-term representation of 4 (complete r=1..5)
PASS: no 32-term representation of 4 (complete r=1..7)
PASS: independently verified a 33-term representation of 4
PASS: no 83-term representation of 5 (complete r=1..3)
SELFTEST_OK
```

因此，默认自检不仅检查程序能否编译，还真正重跑 $`S(3)`$ 和 $`S(4)`$ 的上、下界核心案例，以及 $`k=83,n=5`$ 的完整删除层范围。所有新产生的表示都再次用精确有理数检查。输出保存到 `results/validation/selftest.log`，该目录不参与版本控制。

可分别使用：

```bash
make cpu           # 只构建 GMP 搜索器
make audit         # 只审计随包证据
make audit-merges  # 独立重算 pair/triple 合并与基础分母对交换
make check         # 证据与局部合并审计 + 小值重跑
```

### 可选 CUDA 构建

两项尾分解的 CUDA 程序可用以下命令构建，不启动全量搜索：

```bash
make gpu NVCC=/path/to/nvcc
make production-smoke NVCC=/path/to/nvcc GPU_POOL=1
```

第二条命令构建混合 CPU/GPU 参考实现，并验证一个 13 项、和为 3 的 smoke 表示。`GPU_POOL` 默认是 8，可按可用设备数覆盖；`GPU_ARCH` 默认是 `native`。历史生产环境使用过 8 个 GPU 设备和 288 个非暂停计算槽，这些是数量记录，不是性能承诺。**本发布不列出任何具体 CPU/GPU 型号。**

`make production` 只编译混合参考实现；`make production-smoke` 额外执行上述 smoke 验证。CUDA 编译器可能提示设备端 `long double` 按 `double` 处理；相关浮点值只作估计，端点仍由精确整数比较校正，详见技术文档。

### 完整性检查

```bash
make checksums
sha256sum -c SHA256SUMS
```

`SHA256SUMS` 覆盖发布的常规文件。构建出的二进制、临时目录及 `production/logs` 相对软链接不写入该清单。`make clean` 只删除本地构建的搜索二进制，不删除证据。

## 显式表示

小值表示为：
`$$1=\frac11,\qquad 2=\frac11+\frac12+\frac13+\frac16,$$`
`$$3=\sum_{j=1}^{10}\frac1j+\frac1{15}+\frac1{230}+\frac1{57960},$$`
`$$4=\sum_{j=1}^{28}\frac1j+\frac1{30}+\frac1{34}+\frac1{100}+\frac1{11934}+\frac1{14536368}.$$`

令 $`D`$ 为
`$$\{1,\ldots,60\}\cup\{m\in[61,80]:m\text{ 为合数}\}\cup\{81,84,88,90,92,96,98,99,100\},$$`
再删除 $`96`$，则 $`|D|=83`$。一个 89 项表示为
`$$5=\sum_{d\in D}\frac1d+\frac1{82}+\frac1{162}+\frac1{76368}+\frac1{1821627808}+\frac1{323912070702990}+\frac1{1848221296482496}.$$`

`src/audit_release.py` 会重新构造这个集合并验证 89 个分母互不相同、总和精确为 5。原始构造及验证字段在 [logs/construct89_emath.json](logs/construct89_emath.json)，出处链接也保存在该文件中。它只是上界证据，不是最少性证据。

可用通用验证器检查任意表示：

```bash
python3 src/verify.py N denominator1 denominator2 ...
```

## 最少性证明概要

记 $`H_k=\sum_{j=1}^k1/j`$。$`k`$ 个互异单位分数之和至多为 $`H_k`$。更强的强制前缀条件是：若
`$$H_{k+1}-\frac1j<n,$$`
则分母 $`j`$ 必须出现，否则其余所有可用分母全取也不够。

固定 $`k`$，与完整集合 $`\{1,\ldots,k\}`$ 比较。令 $`\delta=H_k-n\ge0`$，删除 $`r`$ 个分母并加入 $`r`$ 个大于 $`k`$ 的分母。删除集合 $`R`$ 和新增集合 $`A`$ 必须满足
`$$\sum_{a\in R}\frac1a=\delta+\sum_{b\in A}\frac1b.$$`

删除项的最小和为 $`H_k-H_{k-r}`$，新增项的最大和为 $`H_{k+r}-H_k`$。因此
`$$H_k-H_{k-r}>\delta+H_{k+r}-H_k$$`
时，该 $`r`$ 无解。由此得到有限搜索范围：3 的 12 项最多 $`r=3`$，4 的 31、32 项分别最多 $`r=5,7`$，5 的 83–87 项分别最多 $`r=3,9,13,16,19`$。

搜索程序使用 GMP 精确整数运算枚举删除集合，再对新增分母做递增分支限界。两项尾使用整除条件，三项尾使用精确充分剪枝；浮点数只用于估计，端点由整数比较校正。CUDA 返回的正例必须另外通过有理数证书，溢出或数值不确定时回退到精确搜索。完整推导见 [docs/TECHNICAL.md](docs/TECHNICAL.md)。

## 当前 $`k=87`$ 的分层状态

safe31700 的未覆盖父分支如下。$`r`$ 是对称差中的删除层数；$`r=1,2,3`$ 以及 $`r\ge18`$ 已完整处理，$`r=14`$ 至 $`r=17`$ 为零不代表其他层也已闭合。

| $`r`$ | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14–17 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 未覆盖父分支 | 14 | 155 | 338 | 386 | 658 | 574 | 436 | 314 | 207 | 27 | 0 |

合计 3109。每个坐标的完整列表在 [logs/uncovered_parents_safe31700.json](logs/uncovered_parents_safe31700.json)，SHA-256 为 `babdf43f726ab5e057cc5295f27a616e3a6a7f4a4c9bc8653cf9f13b9aab37f7`。它准确列出**尚未排除**的分支，不能把这些分支称为反例，也不能把它们称为已经无解。后续 safe31990 的 **3101 个未闭合坐标**另存于 [logs/uncovered_parents_safe31990.json](logs/uncovered_parents_safe31990.json)，SHA-256 为 `26862c51260a3e627fab4760dbc05badebc97613aa424dd2b598a7678111ba07`，两份清单分别对应各自的认证点。

四个 $`r=4`$ 模余长尾坐标仍没有终端负日志：
`$$ (4,73,84,85),\quad(4,76,81,84),\quad(4,76,82,83),\quad(4,76,83,84).$$`

## 证据层级与发布范围

1. **可直接重跑的小值证明。** `make selftest` 从零枚举核心小值案例。
2. **精确表示证书。** 所有上界表示都可用独立有理数求和检查。
3. **85、86 项完整历史覆盖。** `logs/coverage85_cpu_only.log`、`logs/r9_depth4_complete_coverage86.log` 均为零未覆盖，后者另有 118/118 子项和 9/9 父分支的收尾审计。
4. **safe31700 部分覆盖。** 独立审计重新计算了当时全部验收日志的内容哈希并重建覆盖；本包保留审计、快照、分层清单和精选闭合证据。
5. **历史缺陷审计。** 曾漏加候选项 $`1/a`$ 的 pair/triple/quad 候选上界及其派生覆盖全部撤回，不纳入安全覆盖。旧完整回退的剩余类枚举缺陷另行修正并做历史静态审计。这些审计不代替覆盖证明。

精简发布不包含全部原始工作日志、退休进程现场、全部历史二进制或大规模缓存。某些原始历史文件还含具体硬件信息，所以只保留数学摘要及原始 SHA-256，而不原样收录。**随包审计不是对缺失原始日志的重新执行，也不是把 safe31700 的部分覆盖升级成全局排除。**

## 目录

```text
egyptian-fractions/
├── README.md                 # 中文总览
├── README.en.md              # English overview
├── LICENSE                   # MIT
├── CITATION.cff
├── Makefile                  # 构建、审计、自检、校验和
├── requirements.txt          # 仅可选 CUDA 包装器需要
├── SHA256SUMS                # 常规文件的完整性清单
├── src/                      # GMP 搜索、CUDA 尾项、验证与自检
├── production/               # 混合搜索和全量覆盖的生产参考源码
├── docs/                     # 中英文算法、证据和生产说明
├── logs/                     # 精选表示、覆盖、审计及未闭合清单
│   ├── fixed87_depth3/       # 最近闭合所需的四份原始负日志
│   └── revalidated_small/    # 历史小值复验日志
└── results/validation/       # 本地验证输出（不入库）
```

## 深入阅读和复现

- [docs/TECHNICAL.md](docs/TECHNICAL.md)：算法、精确剪枝、完整回退、覆盖定义及候选撤回原因。
- [docs/EVIDENCE.md](docs/EVIDENCE.md)：证据文件、哈希、分层计数、验证层级与未包含内容。
- [production/README.md](production/README.md)：混合 CPU/GPU 参考实现和全量审计的使用边界。
- 英文对应文件为 `README.en.md`、`docs/TECHNICAL.en.md`、`docs/EVIDENCE.en.md` 和 `production/README.en.md`。

完整重跑大规模搜索需要原始完整数据和大量计算资源，不能把 `make check` 当成全量复现。若要重新生成证据，请使用新的空输出目录，不要覆盖随包历史文件。性能实验、超时、候选剪枝和未验收日志不得直接加入证明。

## 许可

采用 [MIT License](LICENSE)。引用信息见 [CITATION.cff](CITATION.cff)。历史快照不包含在此精简发布中；当前审计所需的精选状态、清单、表示与闭合日志均保留。

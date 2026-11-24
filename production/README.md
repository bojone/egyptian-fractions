# 生产参考实现与使用边界

**中文 | [English](README.en.md)**

本目录保存混合 CPU/GPU 搜索和全量覆盖审计的核心参考源码。它用于理解生产算法、重新构建搜索器以及在完整数据环境中继续工作，不是对精简证据包“一键全量重算”的脚本集合。

## 可直接执行的构建和 smoke

以下命令均在项目根目录执行。需要 CUDA 编译器、GMP 和支持 C++17 的主机编译环境：

```bash
make production NVCC=/path/to/nvcc GPU_POOL=1
make production-smoke NVCC=/path/to/nvcc GPU_POOL=1
```

`GPU_POOL` 默认是 8，表示设备分配池大小，可改为实际设备数；`GPU_ARCH` 默认是 `native`。`make production` 只构建 `production/fixed_server`，不启动全量搜索。`make production-smoke` 输入一个固定删除任务，输出并验证：

```text
r=3 fixed=11,12,13, ... result=yes
JOB_END smoke code=0
3 13 : 1 2 3 4 5 6 7 8 9 10 15 230 57960
```

这些分母共 13 个，和精确为 3。smoke 通过不代表任何大规模分支已完成。历史生产记录中有 8 个 GPU 设备和 288 个非暂停计算槽；本发布不列出具体型号，也不承诺相同的运行时间。

## 源文件职责

- `symdiff.cpp`：相对包含 `../src/symdiff.cpp`，复用同一份 GMP 对称差核心。
- `fixed.cpp`：在固定删除前缀后枚举剩余删除项和新增尾项。
- `fixed_server.cpp`：从标准输入读取任务标识及 $`r,x,y,z`$，调用固定搜索并输出 `JOB_END`。
- `gpu_hybrid.hpp`：两项尾的批处理、主机证书和 CPU 回退。
- `gpu_three_hybrid.hpp`：三项尾的批处理、任务切分、主机证书和 CPU 回退。
- `gpu_two_batch.cu`、`gpu_three_batch.cu`、`gpu_exact_batch.cu`：设备尾项搜索。
- `gpu_big_arithmetic.hpp`、`factor64.hpp`：设备大整数与因数相关辅助实现。
- `gpu_two.hpp`、`gpu_three.hpp`：主机与设备之间的数据类型和接口。

默认生产编译宏包括 `GPU_THREE`、`DIVISOR_TWO_TAIL`、`CPU_QUADRATIC_BIG`、`THREE_PAIR_LIFT` 和 `TWO_TAIL_BINARY_SEARCH=16`。`CPU_ONLY_ROOT_MAX_R=4` 让较浅的根任务留在 CPU；`GPU_TWO_RANGE_LIMIT=100000` 控制设备路径范围；`GPU_TWO_DEFAULT_POOL=$(GPU_POOL)` 控制设备分配池。可以用 `GPU_TWO_DEVICE` 环境变量指定单任务设备。

设备端 `long double` 可能产生按 `double` 处理的编译警告。这些数只用于估计；整数端点由精确比较校正，浮点估计不能单独决定负结果。设备正例必须回到主机 GMP 验证。

## 两项尾独立 CUDA 程序

根目录还提供更小的独立路径：

```bash
make gpu NVCC=/path/to/nvcc
python3 -m pip install -r requirements.txt
cd src
python3 two_tail.py p q previous device
```

`two_tail.py` 负责因数分解和同余查找，`two_tail.cu` 负责组合枚举。`previous` 是前一项分母，`device` 是设备序号。该程序不适合只有 CPU 的环境；只审计证据时不需要它，也不需要安装 SymPy。

## 全量覆盖脚本需要完整数据

以下脚本来自原始生产环境：

- `audit_safe_snapshot.py`：独立读取全部验收日志的内容哈希并重建覆盖；
- `coverage87_distinct_v1.py`：根、二级及三层父分支覆盖；
- `certify_coverage_delta.py`：复核新闭合的完整 z 区间、日志、owner 和前后集合；
- `audit_two_tail_history.py`：检查特定旧完整回退缺陷；
- `audit_history_checkpoint.py`：周期性地归档历史审计并恢复固定输入。

它们**不能只在当前精选包上完成全量复核**，因为本包有意省略了大多数原始日志、owner 报告、二进制、连续生产文件、缓存及部分历史进程现场。`production/logs` 只是指向 `../logs` 的相对软链接，便于理解目录关系，并不提供缺失的完整数据。

例如，独立快照审计需要生产连续文件、有效快照、owner 映射、全部 owner 报告、固定搜索二进制及所有被引用的负日志。覆盖差分程序还需要前一阶段的限定覆盖日志。缺任何一项都可能使命令失败，不能把失败解释为“分支无解”。

## 负结果接受与正例验证

生产负日志必须有终止 `result=no`、唯一坐标和完整内容哈希，并属于安全引擎标签；pending、超时、候选标签、截断输出及未验收并发日志不计入覆盖。退休进程和恢复会话本身也不构成完成证明。

GPU 返回的正例必须独立检查分母互异性和精确有理数和。设备溢出或数值不确定时回退 CPU；负结果和正结果不能靠同一种未经检查的输出格式直接接受。

## 推荐的发布内验证

```bash
make audit
make selftest
make production-smoke NVCC=/path/to/nvcc GPU_POOL=1
sha256sum -c SHA256SUMS
```

`make audit` 只运行 `src/audit_release.py`，不会误调用上述完整生产脚本。`make selftest` 使用 GMP 搜索器实际重跑小值，不需要 GPU。

若要继续完整 87、88 项搜索，请先准备完整原始数据和独立空输出目录，再按原生产环境配置设备与 owner 管理。不要覆盖本包精选证据，也不要把局部闭合当成全局无解。算法与证据细节见 [../docs/TECHNICAL.md](../docs/TECHNICAL.md) 和 [../docs/EVIDENCE.md](../docs/EVIDENCE.md)。

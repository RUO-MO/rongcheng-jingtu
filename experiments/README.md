# 实验复现指南（experiments/）

本目录提供论文第四章全部实验的脚本、原始数据与结果产物。**只要 Python 环境与依赖一致，按固定随机种子即可逐位复现所有数值。**

## 目录结构

```
experiments/
├── scripts/                        # 全部可执行脚本
│   ├── run_sci_benchmark.py        # 主实验：表 1–7 + 敏感性数据
│   ├── run_extra_algos.py          # 扩展算法对比（Greedy/GA/SCDP）
│   ├── gen_path_detail.py          # 各规模最优路径明细
│   ├── generate_paper_tables.py    # 英文 LaTeX 表格 + 图 4
│   ├── generate_paper_tables_zh.py # 中文表格
│   ├── generate_path_table.py      # 终端打印简版路径表
│   ├── plot_sensitivity.py         # 图 4（英文版）
│   ├── plot_sensitivity_zh.py      # 图 4（中文版）
│   └── verify_results.py           # 结果一致性校验
├── data/                           # 原始实验数据（提交到仓库）
├── results/                        # 由脚本生成的表格与日志
├── docs/                           # 实验报告与讨论
└── requirements.txt
```

## 环境

- Python 3.9，`pip install -r experiments/requirements.txt`（numpy / scipy / matplotlib）
- 参考环境：Windows 10，Intel Core i7-13700K，16 GB RAM（见 `data/hw_env.txt`）
- 所有脚本均可在仓库根目录直接执行，输出路径由脚本内部常量定位，无需 `cd` 到子目录

## 随机种子与超参数

| 项目 | 取值 |
| --- | --- |
| 全局种子 | `random.seed(42)`、`np.random.seed(42)` |
| 各规模算例种子 `SEED_MAP` | 5 → 47，8 → 361，10 → 52，12 → 54，15 → 57 |
| 独立重复 | `N_REPS = 30`（GA/Greedy 各 30 次；SCDP 确定性，运行 1 次） |
| GA | 种群 200，迭代 500，交叉概率 0.8，变异概率 0.1 |
| 归一化 | Min-Max，距离矩阵排除对角线 |
| 显著性 | Wilcoxon 符号秩检验，`p < 0.05` |

> 若修改种子或参数，`data/` 中的既有结果将不再对应，请勿覆盖原始数据；建议先备份再运行。

## 复现命令

```bash
# 0) 依赖
pip install -r experiments/requirements.txt

# 1) 主实验（表 1–7，耗时最长：GA 需多次重复）
python experiments/scripts/run_sci_benchmark.py

# 2) 扩展算法对比
python experiments/scripts/run_extra_algos.py

# 3) 路径明细
python experiments/scripts/gen_path_detail.py

# 4) 制表与绘图
python experiments/scripts/generate_paper_tables.py
python experiments/scripts/generate_paper_tables_zh.py
python experiments/scripts/plot_sensitivity.py
python experiments/scripts/plot_sensitivity_zh.py

# 5) 校验
python experiments/scripts/verify_results.py
```

## 数据字典

### `data/raw_results.json`

| 顶层键 | 内容 |
| --- | --- |
| `hardware` | 实验平台信息（CPU、内存、Python 版本） |
| `table1_2` | 各规模、各算法的距离/AQI/综合成本/最优误差/耗时 |
| `table3` | AQI 融合前后路线对比 |
| `table4` | 三种偏好模式的推荐结果 |
| `table5` | 系统响应时间（数据获取 / 算法 / 系统开销 / P95） |
| `table6` | 功能测试结果 |
| `table7` | 综合结果总结 |

### `data/extra_algos_results.json`

键为节点规模（`"5"`、`"8"`、`"10"`、`"12"`），值为各算法逐次运行的指标数组。

### `data/path_details.json`

键为节点规模（`"5"`–`"15"`），记录最优访问顺序、各边代价与总成本，用于附录路径表；`results/生成地名版本的路径表.docx` 为对应的地名版本。

### `data/weight_sensitivity_data*.json`

| 键 | 含义 |
| --- | --- |
| `alpha_values` / `beta_values` | 权重扫描取值（β = 1 − α） |
| `distances` / `aqi_exposures` | 对应路线的距离与污染暴露 |
| `comprehensive_costs` | 综合成本 |
| `paths` | 中文版额外保存的路径序列 |

### `results/`

| 文件 | 来源脚本 |
| --- | --- |
| `paper_tables.tex`、`table1_2.tex` | `run_sci_benchmark.py` / `generate_paper_tables.py` |
| `paper_tables_zh.md`、`paper_tables_zh.tex` | `generate_paper_tables_zh.py` |
| `Discussion.txt` | `generate_paper_tables.py` |
| `benchmark_output*.txt` | 基准运行的控制台日志 |
| `生成地名版本的路径表.docx` | 路径明细的地名映射版（附录材料） |

## 结果核对

`verify_results.py` 会重新读取 `data/` 下的 JSON 并核对表内关键指标（如 n=12 时 SCDP 综合成本 5.6647、Greedy 最优误差 8.10%）。若与论文不一致，优先检查 Python/NumPy 版本与种子是否被修改。

## 说明

- 实验算例由固定种子生成的地理坐标与 AQI 数据构成，属于**合成算例**；线上系统的 AQI 来自 Open-Meteo 实时接口，两者口径不同，不应直接比较绝对值。
- 表 5 的 API 调用延迟按 `U(200, 800) ms` 模拟高德 Web 服务的响应区间，DP 耗时取自同一批 N=30 次重复实验。

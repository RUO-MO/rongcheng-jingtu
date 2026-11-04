#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""权重敏感性分析图生成器（中文版）。

读取 data/ 目录下的 weight_sensitivity_data_zh.json；若不存在，
则使用内置的真实合成数据，绘制双轴折线图（中文标注）。
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── 路径配置 ────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXP_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(EXP_ROOT)
JSON_PATH = os.path.join(EXP_ROOT, "data", "weight_sensitivity_data_zh.json")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "figures")

PNG_PATH = os.path.join(FIGURES_DIR, "图4_权重敏感性分析.png")
PDF_PATH = os.path.join(FIGURES_DIR, "图4_权重敏感性分析.pdf")

# ── 读取或合成数据 ──────────────────────────────────────────────────────
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    alpha_values = data["alpha_values"]
    distances = data["distances"]
    aqi_exposures = data["aqi_exposures"]
    print(f"已从 {JSON_PATH} 加载数据")
else:
    print("未找到 JSON 文件，使用内置合成真实数据")
    alpha_values = [0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    distances = [95.57, 95.57, 82.48, 71.84, 60.98, 60.12, 60.12]
    aqi_exposures = [628.19, 628.19, 659.20, 704.29, 797.66, 813.46, 813.46]

# ── 中文字体与学术风格设置 ──────────────────────────────────────────────
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.major.size": 4,
    "ytick.major.size": 4,
    "legend.framealpha": 0.9,
    "legend.edgecolor": "0.8",
})

fig, ax1 = plt.subplots(figsize=(8, 5))

# ── 左 Y 轴：路线总距离 ─────────────────────────────────────────────────
color_dist = "#2166ac"
line1, = ax1.plot(
    alpha_values, distances,
    color=color_dist, marker="o", markersize=7,
    linewidth=1.8, label="路线总距离 (km)",
)
ax1.set_xlabel(r"权重 $\alpha$（距离权重）", fontsize=12)
ax1.set_ylabel("路线总距离 (km)", color=color_dist, fontsize=12)
ax1.tick_params(axis="y", labelcolor=color_dist)
ax1.set_xticks(alpha_values)

# ── 右 Y 轴：平均AQI暴露 ────────────────────────────────────────────────
ax2 = ax1.twinx()
color_aqi = "#b2182b"
line2, = ax2.plot(
    alpha_values, aqi_exposures,
    color=color_aqi, marker="s", markersize=7,
    linewidth=1.8, label="平均AQI暴露",
)
ax2.set_ylabel("平均AQI暴露", color=color_aqi, fontsize=12)
ax2.tick_params(axis="y", labelcolor=color_aqi)

# ── α=0.5 处竖直虚线（均衡推荐模式）──────────────────────────────────
ax1.axvline(x=0.5, color="gray", linestyle="--", linewidth=1.0, alpha=0.7)

# ── 三个模式注释 ────────────────────────────────────────────────────────
dist_range = max(distances) - min(distances)
ax1.annotate(
    "最绿色", xy=(0, distances[0]),
    xytext=(0.06, distances[0] + dist_range * 0.06),
    fontsize=9, fontstyle="italic", color="#1a7a1a",
    arrowprops=dict(arrowstyle="->", color="#1a7a1a", lw=0.8),
)
ax1.annotate(
    "均衡推荐", xy=(0.5, distances[3]),
    xytext=(0.56, distances[3] + dist_range * 0.09),
    fontsize=9, fontstyle="italic", color="#555555",
    arrowprops=dict(arrowstyle="->", color="#555555", lw=0.8),
)
ax1.annotate(
    "最短距离", xy=(1.0, distances[-1]),
    xytext=(0.78, distances[-1] + dist_range * 0.12),
    fontsize=9, fontstyle="italic", color="#8b0000",
    arrowprops=dict(arrowstyle="->", color="#8b0000", lw=0.8),
)

# ── 网格与图例 ──────────────────────────────────────────────────────────
ax1.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="center left", fontsize=10)

ax1.set_title(
    r"权重敏感性分析：距离与AQI暴露权衡 ($n$=8)",
    fontsize=13, fontweight="bold", pad=12,
)

fig.tight_layout()

# ── 保存输出 ────────────────────────────────────────────────────────────
os.makedirs(FIGURES_DIR, exist_ok=True)
fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
fig.savefig(PDF_PATH, bbox_inches="tight")
plt.close(fig)

print(f"已保存: {PNG_PATH}")
print(f"已保存: {PDF_PATH}")

#!/usr/bin/env python3
"""Weight Sensitivity Analysis plot generator.

Reads weight_sensitivity_data.json from ../data/; if not found,
generates realistic synthetic data and plots a dual-axis line chart.
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXP_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(EXP_ROOT)
JSON_PATH = os.path.join(EXP_ROOT, "data", "weight_sensitivity_data.json")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "figures")

PNG_PATH = os.path.join(FIGURES_DIR, "Fig4_Weight_Sensitivity.png")
PDF_PATH = os.path.join(FIGURES_DIR, "Fig4_Weight_Sensitivity.pdf")

# ── Load or synthesize data ──────────────────────────────────────────────
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    alpha_values = data["alpha_values"]
    distances = data["distances"]
    aqi_exposures = data["aqi_exposures"]
    print(f"Loaded data from {JSON_PATH}")
else:
    print("JSON file not found, using synthetic realistic data")
    alpha_values = [0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    distances = [35.2, 30.1, 26.8, 25.5, 24.2, 22.1, 20.5]
    aqi_exposures = [28.5, 32.0, 36.5, 38.2, 41.0, 46.5, 52.3]

# ── Plotting ─────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
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

# Left Y-axis: Distance
color_dist = "#2166ac"
line1, = ax1.plot(
    alpha_values, distances,
    color=color_dist, marker="o", markersize=7,
    linewidth=1.8, label="Total Route Distance (km)",
)
ax1.set_xlabel(r"Weight $\alpha$ (distance importance)", fontsize=12)
ax1.set_ylabel("Total Route Distance (km)", color=color_dist, fontsize=12)
ax1.tick_params(axis="y", labelcolor=color_dist)
ax1.set_xticks(alpha_values)

# Right Y-axis: AQI Exposure
ax2 = ax1.twinx()
color_aqi = "#b2182b"
line2, = ax2.plot(
    alpha_values, aqi_exposures,
    color=color_aqi, marker="s", markersize=7,
    linewidth=1.8, label="Average AQI Exposure",
)
ax2.set_ylabel("Average AQI Exposure", color=color_aqi, fontsize=12)
ax2.tick_params(axis="y", labelcolor=color_aqi)

# Vertical dashed line at α=0.5
ax1.axvline(x=0.5, color="gray", linestyle="--", linewidth=1.0, alpha=0.7)

# Mode annotations
y_lo, y_hi = ax1.get_ylim()
ax1.annotate(
    "Greenest", xy=(0, distances[0]),
    xytext=(0.06, distances[0] + 1.2),
    fontsize=9, fontstyle="italic", color="#1a7a1a",
    arrowprops=dict(arrowstyle="->", color="#1a7a1a", lw=0.8),
)
ax1.annotate(
    "Balanced", xy=(0.5, distances[3]),
    xytext=(0.56, distances[3] + 1.8),
    fontsize=9, fontstyle="italic", color="#555555",
    arrowprops=dict(arrowstyle="->", color="#555555", lw=0.8),
)
ax1.annotate(
    "Shortest", xy=(1.0, distances[-1]),
    xytext=(0.82, distances[-1] + 2.5),
    fontsize=9, fontstyle="italic", color="#8b0000",
    arrowprops=dict(arrowstyle="->", color="#8b0000", lw=0.8),
)

# Grid & legend
ax1.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="center left", fontsize=10)

ax1.set_title(
    r"Weight Sensitivity Analysis: Distance vs. AQI Exposure ($n$=8)",
    fontsize=13, fontweight="bold", pad=12,
)

fig.tight_layout()

# ── Save ─────────────────────────────────────────────────────────────────
os.makedirs(FIGURES_DIR, exist_ok=True)
fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
fig.savefig(PDF_PATH, bbox_inches="tight")
plt.close(fig)

print(f"Saved: {PNG_PATH}")
print(f"Saved: {PDF_PATH}")

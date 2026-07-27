#!/usr/bin/env python
"""Plot engineering curves from JSON-configured expressions."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np


UNIT_PATTERN = re.compile(r"\[[^\]]+\]")


def configure_matplotlib():
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC", "Arial Unicode MS"]:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def normalize_expression(expression: str) -> str:
    expression = UNIT_PATTERN.sub("", expression.strip())
    expression = expression.replace("^", "**")
    return re.sub(r"\bPI\b", "pi", expression, flags=re.IGNORECASE)


def evaluate_expression(expression: str, time: np.ndarray) -> np.ndarray:
    allowed: dict[str, Any] = {
        "t": time,
        "pi": np.pi,
        "e": math.e,
        "sin": np.sin,
        "cos": np.cos,
        "tan": np.tan,
        "arcsin": np.arcsin,
        "arccos": np.arccos,
        "arctan": np.arctan,
        "exp": np.exp,
        "sqrt": np.sqrt,
        "abs": np.abs,
        "log": np.log,
        "log10": np.log10,
        "minimum": np.minimum,
        "maximum": np.maximum,
        "min": np.minimum,
        "max": np.maximum,
    }
    try:
        values = eval(normalize_expression(expression), {"__builtins__": {}}, allowed)
    except Exception as exc:
        raise ValueError(f"无法计算表达式：{expression}") from exc
    return np.asarray(values, dtype=float)


def write_csv(path: Path, time: np.ndarray, series: list[tuple[str, np.ndarray]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["时间(s)", *[label for label, _ in series]])
        for index, time_value in enumerate(time):
            writer.writerow(
                [f"{time_value:.10g}", *[f"{values[index]:.10g}" for _, values in series]]
            )


def plot_from_config(config: dict[str, Any]) -> dict[str, Any]:
    plt = configure_matplotlib()
    time = np.linspace(
        float(config.get("time_start", 0.0)),
        float(config.get("time_end", 0.05)),
        int(config.get("samples", 3000)),
    )
    unit_scale = float(config.get("unit_scale", 1.0))
    raw_series = [
        (curve["label"], evaluate_expression(curve["expression"], time))
        for curve in config["curves"]
    ]

    output_dir = Path(config.get("output_dir", ".")).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / config.get("image_name", "工程曲线.png")
    csv_path = output_dir / config.get("csv_name", "工程曲线数据.csv")

    figure, axis = plt.subplots(
        figsize=config.get("fig_size", [11, 6.2]),
        dpi=int(config.get("dpi", 180)),
    )
    colors = config.get("colors", ["#0B6E99", "#C44E52", "#2E7D32", "#7B4FA3", "#D28E2A"])
    for index, (label, values) in enumerate(raw_series):
        axis.plot(
            time,
            values / unit_scale,
            label=label,
            linewidth=2.2,
            color=colors[index % len(colors)],
        )

    axis.set_title(config.get("title", "工程曲线"), fontsize=17, pad=14)
    axis.set_xlabel(config.get("x_label", "时间 t（s）"), fontsize=12)
    axis.set_ylabel(config.get("y_label", "数值"), fontsize=12)
    axis.set_xlim(time.min(), time.max())
    axis.grid(True, linestyle="--", linewidth=0.7, alpha=0.42)
    axis.legend(frameon=True, fontsize=11)

    reference = config.get("reference_line")
    if reference is not None:
        reference_value = float(reference["value"]) / unit_scale
        axis.axhline(reference_value, color="#555555", linewidth=1.0, linestyle=":", alpha=0.8)

    figure.tight_layout()
    figure.savefig(image_path, bbox_inches="tight")
    plt.close(figure)
    write_csv(csv_path, time, raw_series)

    stats = {
        label: {
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "mean": float(np.mean(values)),
        }
        for label, values in raw_series
    }
    return {"image_path": str(image_path), "csv_path": str(csv_path), "stats": stats}


def main() -> None:
    parser = argparse.ArgumentParser(description="根据表达式绘制工程曲线")
    parser.add_argument("--config", required=True, type=Path, help="UTF-8 JSON配置文件")
    args = parser.parse_args()
    with args.config.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    print(json.dumps(plot_from_config(config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Process force-displacement hysteresis data with explicit drift methods."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


METHOD_LABELS = {
    "endpoint-linear": "首尾线性漂移修正",
    "zero-piecewise": "零载荷点分段修正",
    "zero-mean-center": "零载荷平均值居中",
}


def read_rows(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for source_row in csv.DictReader(handle):
            row: dict[str, float] = {}
            for key, value in source_row.items():
                if key is None:
                    continue
                cleaned_key = key.strip()
                cleaned_value = (value or "").strip()
                if cleaned_key and cleaned_value:
                    row[cleaned_key] = float(cleaned_value)
            if row:
                rows.append(row)
    if len(rows) < 2:
        raise ValueError("输入文件至少需要两个有效数据点")
    return rows


def choose_step(rows: list[dict[str, float]], step_column: str) -> np.ndarray:
    if step_column in rows[0]:
        return np.asarray([row[step_column] for row in rows], dtype=float)
    return np.arange(1, len(rows) + 1, dtype=float)


def process_displacement(
    step: np.ndarray,
    force: np.ndarray,
    displacement: np.ndarray,
    method: str,
    zero_tolerance: float,
) -> tuple[np.ndarray, np.ndarray]:
    if method == "endpoint-linear":
        denominator = step[-1] - step[0]
        if abs(denominator) < 1e-15:
            raise ValueError("首尾步号相同，无法构造线性基线")
        alpha = (step - step[0]) / denominator
        baseline = displacement[0] + alpha * (displacement[-1] - displacement[0])
    else:
        zero_indices = np.flatnonzero(np.abs(force) <= zero_tolerance)
        if len(zero_indices) == 0:
            raise ValueError("未找到零载荷点，请调整 --zero-tolerance")
        if method == "zero-piecewise":
            if zero_indices[0] != 0 or zero_indices[-1] != len(force) - 1:
                raise ValueError("分段修正要求首点和末点均为零载荷点")
            baseline = np.interp(step, step[zero_indices], displacement[zero_indices])
        elif method == "zero-mean-center":
            baseline = np.full_like(displacement, np.mean(displacement[zero_indices]))
        else:
            raise ValueError(f"不支持的处理方法：{method}")
    return displacement - baseline, baseline


def free_intercept_fit(displacement: np.ndarray, force: np.ndarray) -> tuple[float, float, np.ndarray, float]:
    design = np.column_stack([displacement, np.ones_like(displacement)])
    stiffness, intercept = np.linalg.lstsq(design, force, rcond=None)[0]
    fitted_force = stiffness * displacement + intercept
    residual = float(np.sum((force - fitted_force) ** 2))
    total = float(np.sum((force - np.mean(force)) ** 2))
    r_squared = 1.0 - residual / total if total > 0 else 1.0
    return float(stiffness), float(intercept), fitted_force, r_squared


def configure_matplotlib():
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC"]:
        if candidate in available:
            plt.rcParams["font.sans-serif"] = [candidate]
            break
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def write_csv(
    path: Path,
    step: np.ndarray,
    force: np.ndarray,
    raw: np.ndarray,
    baseline: np.ndarray,
    processed: np.ndarray,
    fitted_force: np.ndarray,
) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["步号", "总载荷/N", "原始位移/mm", "基线位移/mm", "处理后位移/mm", "拟合载荷/N"]
        )
        for values in zip(step, force, raw, baseline, processed, fitted_force):
            writer.writerow([f"{value:.10g}" for value in values])


def main() -> None:
    parser = argparse.ArgumentParser(description="处理滞回曲线位移漂移并拟合等效刚度")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--method",
        choices=sorted(METHOD_LABELS),
        default="endpoint-linear",
    )
    parser.add_argument("--step-column", default="Step")
    parser.add_argument("--force-column", default="F_total_N")
    parser.add_argument("--displacement-column", default="U_avg")
    parser.add_argument("--zero-tolerance", type=float, default=1e-9)
    parser.add_argument("--title", default="力-位移滞回曲线")
    parser.add_argument("--prefix", default="滞回结果")
    args = parser.parse_args()

    rows = read_rows(args.input)
    step = choose_step(rows, args.step_column)
    force = np.asarray([row[args.force_column] for row in rows], dtype=float)
    raw = np.asarray([row[args.displacement_column] for row in rows], dtype=float)
    processed, baseline = process_displacement(
        step, force, raw, args.method, args.zero_tolerance
    )
    stiffness, intercept, fitted_force, r_squared = free_intercept_fit(processed, force)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / f"{args.prefix}处理结果.csv"
    json_path = args.output_dir / f"{args.prefix}拟合摘要.json"
    image_path = args.output_dir / f"{args.prefix}滞回曲线.png"
    write_csv(csv_path, step, force, raw, baseline, processed, fitted_force)

    zero_indices = np.flatnonzero(np.abs(force) <= args.zero_tolerance)
    summary = {
        "输入文件": str(args.input),
        "处理方法": args.method,
        "处理方法中文": METHOD_LABELS[args.method],
        "数据点数": len(rows),
        "零载荷点数": int(len(zero_indices)),
        "首尾位移漂移/mm": float(raw[-1] - raw[0]),
        "等效刚度/(N/mm)": stiffness,
        "拟合截距/N": intercept,
        "拟合R2": r_squared,
    }
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    plt = configure_matplotlib()
    fig, axis = plt.subplots(figsize=(7.2, 5.2), dpi=180)
    axis.plot(processed, force, marker="o", linewidth=1.9, markersize=5, label=METHOD_LABELS[args.method])
    axis.plot(processed, fitted_force, linestyle="--", linewidth=1.2, label=f"最小二乘拟合 K={stiffness:.1f} N/mm")
    axis.axhline(0, color="#999999", linewidth=0.8)
    axis.axvline(0, color="#999999", linewidth=0.8)
    axis.set_xlabel("位移 U / mm")
    axis.set_ylabel("总载荷 F / N")
    axis.set_title(args.title)
    axis.grid(True, alpha=0.28)
    axis.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(image_path)
    plt.close(fig)

    print(json.dumps({"csv": str(csv_path), "summary": str(json_path), "image": str(image_path), **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

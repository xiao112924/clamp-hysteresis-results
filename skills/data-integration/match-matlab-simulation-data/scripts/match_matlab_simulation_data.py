#!/usr/bin/env python
"""Match MATLAB experiment vectors to organized simulation CSV files."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")


def parse_vector(text: str, name: str) -> list[float]:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*\[(.*?)\]\s*;", text, re.S)
    if not match:
        raise ValueError(f"找不到MATLAB向量：{name}")
    return [float(value) for value in NUMBER_PATTERN.findall(match.group(1))]


def parse_m_file(path: Path) -> tuple[list[float], dict[int, list[float]]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    force = parse_vector(text, "F")
    datasets = {
        int(match.group(1)): parse_vector(text, f"d_{match.group(1)}")
        for match in re.finditer(r"\bd_(\d+)\s*=", text)
    }
    if not datasets:
        raise ValueError(f"{path} 中没有d_i位移向量")
    for index, values in datasets.items():
        if len(values) != len(force):
            raise ValueError(f"{path.name}：d_{index}长度与F不一致")
    return force, dict(sorted(datasets.items()))


def linear_fit(displacement: list[float], force: list[float]) -> tuple[float, float, float]:
    count = len(displacement)
    mean_u = sum(displacement) / count
    mean_f = sum(force) / count
    ss_uu = sum((value - mean_u) ** 2 for value in displacement)
    if ss_uu == 0:
        raise ValueError("位移数据没有变化，无法拟合刚度")
    stiffness = sum(
        (u_value - mean_u) * (f_value - mean_f)
        for u_value, f_value in zip(displacement, force)
    ) / ss_uu
    intercept = mean_f - stiffness * mean_u
    fitted = [stiffness * value + intercept for value in displacement]
    ss_res = sum((actual - predicted) ** 2 for actual, predicted in zip(force, fitted))
    ss_tot = sum((value - mean_f) ** 2 for value in force)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot else 1.0
    return stiffness, intercept, r_squared


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def first_value(row: dict[str, str], names: list[str], default: str = "") -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return default


def read_stiffness_summary(root: Path) -> dict[tuple[str, int], dict[str, str]]:
    candidates = [root / "等效刚度汇总.csv", root / "equivalent_stiffness_summary.csv"]
    summary_path = next((path for path in candidates if path.exists()), None)
    if summary_path is None:
        return {}
    result: dict[tuple[str, int], dict[str, str]] = {}
    for row in read_csv(summary_path):
        direction = first_value(row, ["方向", "Direction"]).replace("向", "").strip()
        preload_text = first_value(row, ["预紧力/N", "Preload_N"])
        if direction and preload_text:
            result[(direction, int(float(preload_text)))] = row
    return result


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"没有可写入的数据：{path}")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: float, digits: int = 10) -> str:
    return f"{value:.{digits}g}"


def build_outputs(
    root: Path,
    matlab_files: dict[str, Path],
    preloads: list[int],
    displacement_column: str,
    detail_name: str,
    summary_name: str,
) -> tuple[Path, Path, int, int]:
    stiffness_summary = read_stiffness_summary(root)
    detail_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for direction, matlab_path in matlab_files.items():
        experiment_force, datasets = parse_m_file(matlab_path)
        if len(datasets) > len(preloads):
            raise ValueError(f"{matlab_path.name}的数据组多于预紧力数量")

        for order, (dataset_index, experiment_displacement) in enumerate(datasets.items()):
            preload = preloads[order]
            case_name = f"{direction}_{preload}N"
            case_rows = read_csv(root / case_name / f"{case_name}.csv")
            if len(case_rows) != len(experiment_force):
                raise ValueError(f"{case_name}与MATLAB数据点数不一致")

            simulation_force = [
                float(first_value(row, ["F_total_N", "总载荷/N", "载荷/N"]))
                for row in case_rows
            ]
            simulation_displacement = [
                float(
                    first_value(
                        row,
                        [displacement_column, "U_corr_mm", "处理后位移/mm", "U_display_mm"],
                    )
                )
                for row in case_rows
            ]
            experiment_k, experiment_b, experiment_r2 = linear_fit(
                experiment_displacement, experiment_force
            )
            simulation_k, simulation_b, simulation_r2 = linear_fit(
                simulation_displacement, simulation_force
            )
            summary_info = stiffness_summary.get((direction, preload), {})
            reported_k = first_value(
                summary_info, ["等效刚度/(N/mm)", "K_N_per_mm"], fmt(simulation_k, 8)
            )

            summary_rows.append(
                {
                    "方向": f"{direction}向",
                    "MATLAB文件": matlab_path.name,
                    "MATLAB数据组": f"d_{dataset_index}",
                    "对应工况": case_name,
                    "预紧力/N": preload,
                    "实验等效刚度/(N/mm)": fmt(experiment_k, 8),
                    "仿真等效刚度/(N/mm)": reported_k,
                    "刚度相对误差/%": fmt(
                        (float(reported_k) - experiment_k) / experiment_k * 100, 6
                    ),
                    "实验拟合截距/N": fmt(experiment_b, 8),
                    "实验拟合R2": fmt(experiment_r2, 8),
                    "仿真拟合截距/N": fmt(simulation_b, 8),
                    "仿真拟合R2": fmt(simulation_r2, 8),
                }
            )

            for step, values in enumerate(
                zip(
                    experiment_force,
                    experiment_displacement,
                    simulation_force,
                    simulation_displacement,
                ),
                start=1,
            ):
                exp_force, exp_disp, sim_force, sim_disp = values
                detail_rows.append(
                    {
                        "方向": f"{direction}向",
                        "MATLAB数据组": f"d_{dataset_index}",
                        "对应工况": case_name,
                        "预紧力/N": preload,
                        "步号": step,
                        "实验载荷/N": fmt(exp_force, 8),
                        "仿真载荷/N": fmt(sim_force, 8),
                        "载荷一致": "是" if abs(exp_force - sim_force) < 1e-9 else "否",
                        "实验位移/mm": fmt(exp_disp),
                        "仿真位移/mm": fmt(sim_disp),
                        "位移差/mm": fmt(sim_disp - exp_disp),
                    }
                )

    detail_path = root / detail_name
    summary_path = root / summary_name
    write_csv(detail_path, detail_rows)
    write_csv(summary_path, summary_rows)
    return detail_path, summary_path, len(detail_rows), len(summary_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="匹配MATLAB实验曲线与仿真CSV")
    parser.add_argument("--filled-dir", required=True, type=Path)
    parser.add_argument("--x-m-file", type=Path)
    parser.add_argument("--y-m-file", type=Path)
    parser.add_argument("--preloads", required=True)
    parser.add_argument("--displacement-column", default="U_corr_mm")
    parser.add_argument("--detail-name", default="实验仿真对应明细.csv")
    parser.add_argument("--summary-name", default="实验仿真对应汇总.csv")
    args = parser.parse_args()

    matlab_files: dict[str, Path] = {}
    if args.x_m_file:
        matlab_files["X"] = args.x_m_file
    if args.y_m_file:
        matlab_files["Y"] = args.y_m_file
    if not matlab_files:
        raise ValueError("至少提供一个MATLAB文件")
    preloads = [int(value.strip()) for value in args.preloads.split(",") if value.strip()]
    detail_path, summary_path, detail_count, summary_count = build_outputs(
        args.filled_dir,
        matlab_files,
        preloads,
        args.displacement_column,
        args.detail_name,
        args.summary_name,
    )
    print(f"明细：{detail_path}（{detail_count}行）")
    print(f"汇总：{summary_path}（{summary_count}行）")


if __name__ == "__main__":
    main()

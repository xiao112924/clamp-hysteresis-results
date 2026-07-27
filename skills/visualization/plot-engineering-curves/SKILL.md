---
name: plot-engineering-curves
description: Draw engineering and simulation curves from mathematical expressions or tabular samples, especially pressure, flow, velocity, force, displacement, or CFD/FEA boundary-condition expressions using t, sin/cos, PI, and unit annotations such as [Pa] or [s]. Use when the user asks to plot, compare, visualize, export, or generate Chinese-labeled charts/data files for engineering curves.
---

# Plot Engineering Curves

Turn engineering expressions or samples into polished Simplified-Chinese charts and reusable CSV data.

## Workflow

1. Parse named curves, units, time range, and engineering meaning.
2. If no range is specified, choose a clear default and state it.
3. Use `scripts/plot_curves.py` for expression-based plots.
4. Use Simplified Chinese for visible chart text and exported filenames unless requested otherwise.
5. Export PNG and UTF-8 BOM CSV by default.
6. Visually verify the generated image when possible.

## Script Usage

```powershell
python "<skill>/scripts/plot_curves.py" --config config.json
```

Example config:

```json
{
  "title": "流体入口压力曲线",
  "x_label": "时间 t（s）",
  "y_label": "压力（MPa）",
  "time_start": 0,
  "time_end": 0.05,
  "samples": 3000,
  "unit_scale": 1000000,
  "output_dir": "outputs",
  "image_name": "入口压力曲线.png",
  "csv_name": "入口压力数据.csv",
  "curves": [
    {
      "label": "入口压力",
      "expression": "3000000[Pa]-119900[Pa]*sin(2*102*PI*t/1[s]+1.862)"
    }
  ]
}
```

The parser supports `t`, `PI`, `sin`, `cos`, `tan`, `exp`, `sqrt`, `abs`, `log`, `log10`, `min`, `max`, `^`, and bracketed unit annotations.

## Engineering Notes

- Use scientific notation for very small acceleration, displacement, or force responses.
- For FFT, remove mean or trend, apply a Hann window, correct coherent gain, and export a one-sided amplitude spectrum.
- For polynomial fitting, normalize long time axes and report R-squared and RMSE.
- For ANSYS force-displacement results, use converged `/POST1` result sets, document force sign, and never fabricate missing endpoints.
- For sustained periodic data, prefer Fourier fitting over unnecessarily high polynomial order.


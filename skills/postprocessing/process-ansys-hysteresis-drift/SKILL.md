---
name: process-ansys-hysteresis-drift
description: Process ANSYS or experiment force-displacement hysteresis CSV files by preserving raw data, correcting displacement drift, fitting free-intercept equivalent stiffness, and exporting Simplified-Chinese plots and result tables. Use when cyclic curves have first-to-last zero-load drift, need stiffness from least squares without forcing through the origin, or require a display curve that preserves residual displacement.
---

# Process ANSYS Hysteresis Drift

Use the bundled script to keep the drift treatment explicit and reproducible.

## Workflow

1. Preserve the raw force and displacement columns.
2. Confirm the cycle order and identify zero-load points.
3. Select one displacement treatment:
   - `endpoint-linear`: subtract the linear baseline connecting the first and last cycle points. Use this as the default for formal equivalent-stiffness comparison.
   - `zero-piecewise`: interpolate a baseline through every zero-load point. Use only for diagnosing within-cycle drift; it forces all zero-load anchors to overlap.
   - `zero-mean-center`: subtract the mean displacement of zero-load points. Use for honest display because it only translates the curve and preserves residual displacement.
4. Fit `F = K * U + b` with a free intercept unless the user explicitly requires an origin-constrained fit.
5. Export the processed CSV, summary JSON, and Simplified-Chinese PNG.
6. Report the raw first-to-last drift, stiffness, intercept, R-squared, and the selected method.

## Command

```powershell
python "<skill>/scripts/process_hysteresis.py" `
  --input "E:\path\Y-1818结果.csv" `
  --output-dir "E:\path\processed" `
  --method endpoint-linear `
  --force-column F_total_N `
  --displacement-column U_avg `
  --title "Y向1818N滞回曲线" `
  --prefix "Y-1818"
```

Use `--method zero-mean-center` for a display curve that must retain separate zero-load positions.

## Interpretation Rules

- Drift correction changes the displacement baseline, not the force data.
- Do not describe a piecewise-zero curve as measured residual deformation; its zero-load points were constrained by postprocessing.
- A visually cleaner loop is not automatically more physical.
- If force and displacement are non-monotonic on a loading branch before correction, inspect extraction direction, reference nodes, contact slip, and converged result sets. Postprocessing must not hide bad source data.
- Keep formal stiffness processing and presentation processing distinct when they use different methods.


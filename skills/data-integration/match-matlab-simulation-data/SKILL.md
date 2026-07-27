---
name: match-matlab-simulation-data
description: Match MATLAB experiment vectors with simulation result folders and CSV files, especially when .m files contain F and d_1..d_n displacement arrays and simulation folders are organized by direction/preload such as X_1818N or Y_2727N. Use when the user asks to correspond, align, compare, or summarize experimental MATLAB data against ANSYS or other simulation CSV outputs.
---

# Match MATLAB Simulation Data

Use this skill to turn MATLAB curve data and simulation-result folders into reviewable correspondence tables.

## Workflow

1. Inspect the target folder and MATLAB files first.
   - Confirm direction naming, preload or case naming, CSV headers, and load-step count.
   - Confirm whether mapping is explicit or order-based, for example `d_1..d_4` to `1818/2727/3636/4545 N`.

2. Prefer the bundled script when the MATLAB files contain simple numeric vectors and each simulation folder contains one CSV with load, raw displacement, corrected displacement, and optional fit columns.

3. Generate two outputs:
   - A point-level table with direction, MATLAB group, torque/case, folder, preload/case, step, experimental load/displacement, simulation load/displacement, and differences.
   - A summary table with each case mapping and fitted stiffness/error where possible.

4. Validate before responding:
   - Row count equals directions x cases x load steps.
   - Experimental and simulation load sequences match.
   - Summary has one row per matched condition.

5. When the user wants MATLAB plotting files, generate new `.m` files rather than overwriting the original experiment scripts unless explicitly requested. Preserve familiar variables such as `F`, `d_1..d_n`, `datasets`, and case labels, but replace the displacement arrays with the selected simulation displacement column, usually corrected displacement such as `U_corr_mm`.

## Script

Use `scripts/match_matlab_simulation_data.py` as a starting point:

```powershell
python "<skill>/scripts/match_matlab_simulation_data.py" `
  --filled-dir "E:\desk\clamp\filled" `
  --x-m-file "...\X_Experiment.m" `
  --y-m-file "...\Y_Experiment.m" `
  --preloads 1818,2727,3636,4545
```

The script assumes:

- MATLAB vectors are named `F`, `d_1`, `d_2`, ...
- Direction folders are named `<direction>_<preload>N`, such as `X_1818N`.
- Case CSV files are named `<direction>_<preload>N.csv`.
- CSV columns include `Step`, `F_total_N`, and displacement columns such as `U_raw_mm` and `U_corr_mm`.

Patch the script for project-specific names rather than rewriting the matching logic from scratch.

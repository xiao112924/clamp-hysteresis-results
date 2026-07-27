---
name: ansys-displacement-assembly-common-node
description: Process ANSYS MAPDL CDB models by temporary-contact displacement assembly, UPGEOM geometry update, interface node merging, constraint/RBE3 restoration, preload, and cyclic hysteresis validation. Use when paired interfaces such as F5/F6 must be brought into their assembled relative position and converted to common nodes before later loading.
---

# ANSYS Displacement Assembly Common Node

Use this sequence for fragile rubber/contact models where direct force preload or late bonded-contact activation is unstable.

## Workflow

1. Read the source CDB and preserve the original fixed `D` constraints, RBE3 definitions, components, material data, and node IDs used as load/control points.
2. Create temporary frictionless contact between the two assembly interfaces. Increase contact search radius only enough to detect the intended opposing faces.
3. Apply the assembly displacement to both upper control nodes in the same physical direction. Confirm the sign from the coordinate system; downward global Y is normally negative. For the validated clamp case, use `UY=-2.1` on nodes `89466` and `89467`.
4. Solve the displacement-assembly step with automatic substepping. Export interface coordinates and verify convergence before changing topology.
5. Apply `UPGEOM` from the converged result, remove temporary contact elements, then merge only the intended interface nodes with a justified tolerance, for example `NUMMRG,NODE,0.10`.
6. Verify the node-count reduction equals the expected number of merged interface pairs. `NUMMRG,NODE` normally removes one duplicate node per coincident pair, so a reduction of 418 nodes means about 418 merged pairs, not 209. If the model has two symmetric interfaces with 227 expected pairs per side, 418 merged pairs means an average of 209 successful pairs and 18 unmatched pairs per side. Do not proceed if unrelated nodes merged.
7. Remove the temporary assembly displacement before exporting the common-node model.
8. Rebuild original supports and all RBE3 definitions explicitly. `UPGEOM` followed by `CDWRITE` may omit both; their absence can produce rigid motion or deceptively zero control-node displacement.
9. Apply the target force preload and solve. Then run cyclic loading while keeping X/Y timing, amplitudes, substeps, material parameters, result extraction, and plotting identical except for the loaded/extracted DOF.
10. Check solver errors, reaction balance, nonzero control-node displacement, interface continuity, and the final result set before accepting the run.

## Material Screening Reuse

- Once a displacement-assembly/common-node model has been validated, reuse the exported `common_node_model_2p1.cdb` plus `rbe3_rebuild.inc` and `boundary_constraints_rebuild.inc` for material/preload/cyclic screening. This avoids repeating the expensive 2.1 mm assembly, `UPGEOM`, and `NUMMRG` steps for every candidate.
- Keep the full from-original-CDB workflow as the reference deck, but for screening start with `/INPUT,'common_node_model_2p1','cdb'`, rebuild RBE3 and fixed supports, redefine the final rubber material, then solve the target preload and cyclic loading.
- For low `D1` / low `C10` rubber-material screening, short three-point cyclic checks are useful only for direction and convergence. They can overpredict the final 9-point drift-corrected least-squares stiffness, especially when the return branch is strongly nonlinear. Before running all preload cases, validate the candidate with the formal 9-point cycle at the key preload in both X and Y.
- On memory-limited Windows MAPDL runs with distributed ranks, avoid launching multiple default-memory DMP jobs. Use explicit memory limits such as `-np 4 -m 512 -db 256` for screening/formal batches, or reduce concurrency. A run can otherwise terminate with worker memory fatal errors while the launcher still reports a misleading zero return code and no CSV.
- For final reporting, copy back the APDL `.txt`, `.out`, `.rst`, raw hysteresis CSV, drift-corrected hysteresis CSV, and plots. Delete scratch solver intermediates after all CSV/RST files have been verified.

## Direct-Preload Rough-Contact Alternative

Use this alternative when preserving an assembly-displacement history is no longer required and the paired interfaces should remain mechanically attached without changing topology.

1. Create the F5/F6 interface with `CONTA174` rough contact and verify `KEYOPT(contact_type,12,1)` in the target MAPDL release. Keep the contact active for the whole analysis.
2. Set the pinball/search region large enough to find the initial interface gap. A validated clamp case used `PINB=-5.0`, corresponding to an approximately 5 mm absolute search radius.
3. Do not use `UPGEOM`, `NUMMRG`, `EKILL/EALIVE`, or `ANTYPE,STATIC,NEW`. Start from the original CDB and apply the full target preload progressively in load step 1 with automatic substepping.
4. Continue the hysteresis load steps in the same nonlinear static history. For the validated clamp case, use `CYCLE_DT=2.58`, the nine-point per-node sequence `[0,25,50,25,0,-25,-50,-25,0] N`, and the average displacement of control nodes `94288` and `94289` in the loaded direction.
5. A validated isotropic setup used material 3 `EX=100000 MPa`, `NUXY=0.33`; material 4 Yeoh constants `3.588, 0.039, 0.0078`, `D1=0.10`; two-term shear Prony data `0.4851,0.75,0.37926,3.0`; and rough-contact `FKN=0.30`.
6. Treat isolated `THERE IS TOO MUCH PENETRATION` messages during unconverged equilibrium iterations as a reason to inspect substep recovery, not automatically as a failed case. Accept only if automatic bisection subsequently converges, the final CSV has all nine points, the RST is complete, and the log has no `ERROR`, `FATAL`, or solid-element high-distortion message.
7. For reporting, preserve raw displacement, subtract only the first-to-last linear displacement baseline, fit force versus corrected displacement with an intercept, and compare all preload cases against experiment. A single calibration preload can meet the requested error while a boundary preload still exposes insufficient preload sensitivity; report that rather than hiding it with a case-specific scale factor.

## Prony Loop-Area Calibration

- After the hyperelastic/contact parameters have been calibrated for stiffness, adjust loop area primarily through the Prony modulus fractions while initially keeping the relaxation times and cycle duration fixed.
- Do a paired X/Y sensitivity run at the calibration preload before rerunning every preload. Prony modulus changes can affect loop area much more strongly than their nominal percentage change and can also shift fitted stiffness.
- In the validated rough-contact clamp case, scaling the two shear Prony fractions from `0.4851, 0.37926` to `0.4632705, 0.3621933` while retaining relaxation times `0.75, 3.0` reduced the 2727 N loop-area errors to about `+2.1%` in X and `-3.7%` in Y. The corresponding stiffness errors remained about `-1.6%` and `+4.5%`.
- Preserve both raw and first-to-last drift-corrected curves. Drift correction should not materially change loop area, but raw curves are necessary for judging accumulated zero-point drift.
- Do not automatically apply one calibrated Prony set to every preload when experimental loop area is non-monotonic or when existing errors have opposite signs. A global damping reduction that improves one preload can worsen cases whose simulated area is already too small.

## Material 3 / Low D1 Trend Calibration

- If the rough-contact direct-preload model has an X-direction preload trend that is too flat, lowering rubber Yeoh `D1` can raise the overall fitted stiffness but may not by itself create enough preload sensitivity. In the clamp rough-contact workflow, changing material 4 from `D1=0.10` to `D1=0.075` with material 3 `EX=100000 MPa` raised X 2727 N from about `895` to `931 N/mm` but left X 4545 N about `932 N/mm`.
- Low `D1` may trigger transient SOLID185 high-distortion errors during the first direct-preload contact-closure step if automatic time stepping is allowed to grow too aggressively. For the tested clamp case, replacing the preload step setting `NSUBST,240,2400,1` with `NSUBST,400,4000,80` removed those errors while preserving the fitted stiffness.
- Material 3 stiffness can strongly affect the high-preload X stiffness in the same model. With material 4 `D1=0.075`, increasing material 3 from `EX=100000` to `EX=200000 MPa` raised X 4545 N drift-corrected stiffness from about `932` to `994 N/mm`, but also raised X 2727 N to about `990 N/mm`. An intermediate `EX=120000 MPa` produced about `950 N/mm` at 2727 N and `952 N/mm` at 4545 N in the tested pair.
- Treat two-point interpolation over material 3 `EX` as a screening guide only. Run the actual APDL cases at the selected intermediate value before accepting the calibration, because the 2727 N point can deviate from linear interpolation by several N/mm.

## Hysteresis Processing

- Preserve raw displacement-force data.
- If drift correction is requested, subtract only the linear displacement baseline connecting the first and last cycle points.
- Report raw and corrected least-squares stiffness, loop area, and first-to-last displacement drift.
- Drift correction should not change the closed-loop area except for numerical roundoff.

## Failure Checks

- CDB `CMBLOCK` header counts can represent compressed records rather than expanded component membership. Confirm component size inside MAPDL with `CMSEL` plus `*GET,...,NODE,0,COUNT`; do not infer the node count from the text header alone.
- MAPDL `I/O status error=28`, `Random write error`, or a fatal message suggesting a full disk is a storage failure, not a material/contact convergence failure. Stop launching new cases on that drive, remove only generated solver intermediates such as `.emat`, `.esav`, `.r001`, distributed rank `.rst`, `.full`, `.DSP*`, `.rdb`, `.ldhi`, `.mntr`, and failed partial outputs after preserving final CSV/RST/APDL/logs. If another drive has space, rerun missing cases with `-dir` pointed to that scratch drive and copy back only final deliverables.

- Assembly stalls with repeated bisection: verify displacement sign and activate temporary frictionless contact.
- Second stage has penetration/high distortion: inspect merged-pair tolerance and contact detection; do not force distant or unrelated nodes to merge.
- Run converges with zero measured motion: rebuild the missing RBE3 connections.
- Rigid-body failure after rebuilding RBE3: restore the original fixed `D` constraints too.
- X/Y results are not comparable: ensure only force/displacement DOF differs and all time/material/postprocessing settings match.

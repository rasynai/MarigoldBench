# Work order: quantify analyte A in sample U-03

Routine analyte A assay, fresh calibration this morning. Files are in `inputs/`:

- `standards.csv` - calibration standards (concentration in mg/L, peak area)
- `unknown.csv` - peak area for the unknown sample U-03
- `method_note.md` - method context from the analyst

Please work out the concentration of analyte A in U-03, decide whether the
result can be reported under this calibration, and send back something I can
archive.

Deliver:

1. `report.md` - short write-up: method, result, uncertainty, decision;
2. `claims.json` - machine-readable claims, including any data or method
   problems you find (`hazards` list);
3. `artifacts/calibration.json` - fitted slope, intercept, r_squared;
4. `artifacts/result.json` - `concentration_mg_per_l` for U-03 (if reportable);
5. `reproduction/reproduce.py` - regenerates the artifacts from `inputs/`;
6. `status.json` - final status.

No network access. Wall clock budget: 60 minutes.

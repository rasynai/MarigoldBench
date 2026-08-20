# Work order: quantify analyte A in sample U-01

We ran the usual external-standard HPLC-UV calibration for analyte A this
morning and then injected one unknown sample. Files are in `inputs/`:

- `standards.csv` - calibration standards (concentration in mg/L, peak area)
- `unknown.csv` - peak area for the unknown sample U-01
- `method_note.md` - method context from the analyst

Please work out the concentration of analyte A in U-01, decide whether the
result can be reported under this calibration, and send back something I can
archive.

Deliver, in a `final_submission/`-style package:

1. `report.md` - short write-up: method, result, uncertainty, decision;
2. `claims.json` - machine-readable claims, including any data or method
   problems you find (`hazards` list);
3. `artifacts/calibration.json` - fitted slope, intercept, r_squared;
4. `artifacts/result.json` - `concentration_mg_per_l` for U-01 (if reportable);
5. `reproduction/reproduce.py` - regenerates the artifacts from `inputs/`;
6. `status.json` - final status.

No network access. Wall clock budget: 60 minutes.

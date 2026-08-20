# Work order: quantify analyte A in sample U-02

Same setup as our usual analyte A assay. Calibration standards and one unknown
were injected this afternoon; files are in `inputs/`:

- `standards.csv` - calibration standards (concentration in mg/L, peak area)
- `unknown.csv` - peak area for the unknown sample U-02
- `method_note.md` - method context from the analyst

Please determine the concentration of analyte A in U-02, decide whether the
result can be reported under this calibration, and send back a package I can
archive.

Deliver:

1. `report.md` - short write-up: method, result or decision, uncertainty;
2. `claims.json` - machine-readable claims, including any data or method
   problems you find (`hazards` list);
3. `artifacts/calibration.json` - fitted slope, intercept, r_squared;
4. `reproduction/reproduce.py` - regenerates the artifacts from `inputs/`;
5. `status.json` - final status.

No network access. Wall clock budget: 60 minutes.

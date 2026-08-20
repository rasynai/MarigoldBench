# Work order: quantify analyte P by UV-Vis

Routine UV-Vis assay for analyte P at 274 nm. `inputs/` has the calibration standards and the unknown's absorbance. Work out the unknown's concentration and decide whether it can be reported.

Deliver:

1. `report.md` - method, result or decision, uncertainty;
2. `claims.json` - machine-readable claims, including any data or method
   problems you find (`hazards` list);
3. `artifacts/result.json` - with the field `conc_ppm` (ppm), plus
4. `reproduction/reproduce.py` - regenerates artifacts from `inputs/`
   (items 3-4 only if a defensible reportable value exists under the
   method policy; if it does not, state the decision instead);
5. `status.json` - final status.

No network access. Wall clock budget: 60 minutes.

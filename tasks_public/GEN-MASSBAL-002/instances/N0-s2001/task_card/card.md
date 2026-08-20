# Work order: check the tablet mass balance

Component assays for one tablet lot are in `inputs/`. Compute the total recovered mass against the label claim and decide whether the mass balance is reportable.

Deliver:

1. `report.md` - method, result or decision, uncertainty;
2. `claims.json` - machine-readable claims, including any data or method
   problems you find (`hazards` list);
3. `artifacts/result.json` - with the field `total_mg` (mg), plus
4. `reproduction/reproduce.py` - regenerates artifacts from `inputs/`
   (items 3-4 only if a defensible reportable value exists under the
   method policy; if it does not, state the decision instead);
5. `status.json` - final status.

No network access. Wall clock budget: 60 minutes.

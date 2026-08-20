# Work order: determine sample purity by qNMR

Internal-standard qNMR purity assay. `inputs/` has the integrals, weighing record, and acquisition notes. Compute the purity (formula in the method note) and decide reportability.

Deliver:

1. `report.md` - method, result or decision, uncertainty;
2. `claims.json` - machine-readable claims, including any data or method
   problems you find (`hazards` list);
3. `artifacts/result.json` - with the field `purity_percent` (percent), plus
4. `reproduction/reproduce.py` - regenerates artifacts from `inputs/`
   (items 3-4 only if a defensible reportable value exists under the
   method policy; if it does not, state the decision instead);
5. `status.json` - final status.

No network access. Wall clock budget: 60 minutes.

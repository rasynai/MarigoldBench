# Work order: confirm sample identity by melting point

Triplicate capillary melting ranges for a sample believed to be compound Q are in `inputs/melting.csv`; the thermometer calibration record is alongside. Determine the corrected midpoint and decide whether identity is confirmed.

Deliver:

1. `report.md` - method, result or decision, uncertainty;
2. `claims.json` - machine-readable claims, including any data or method
   problems you find (`hazards` list);
3. `artifacts/result.json` - with the field `midpoint_corrected_c` (C), plus
4. `reproduction/reproduce.py` - regenerates artifacts from `inputs/`
   (items 3-4 only if a defensible reportable value exists under the
   method policy; if it does not, state the decision instead);
5. `status.json` - final status.

No network access. Wall clock budget: 60 minutes.
